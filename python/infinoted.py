"""
This handles the communication to an infinoted server
"""

from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.names.srvconnect import SRVConnector
from twisted.words.xish import domish
from twisted.words.protocols.jabber import xmlstream, client
from twisted.words.protocols.jabber.jid import JID
from twisted.words.protocols.jabber.sasl import SASLInitiatingInitializer
from twisted.python import log


class InfinotedProtocol(object):
    """
    TODO this needs to be examined, probably should be an actual protocol/factory setup
    """
    def __init__(self, service):
        jid = JID('127.0.0.1')
        f = client.XMPPClientFactory(jid, '')
        f.addBootstrap(xmlstream.STREAM_CONNECTED_EVENT, self.connected)
        f.addBootstrap(xmlstream.STREAM_AUTHD_EVENT, self.authenticated)
        connector = SRVConnector(
            reactor, 'xmpp-client', jid.host, f, defaultPort=6523)
        connector.connect()
        self.finished = Deferred()
        self.files = {}
        self.service = service

    def rawDataIn(self, buf):
        log.msg("RECV: %s" % unicode(buf, 'utf-8').encode('ascii', 'replace'))

    def rawDataOut(self, buf):
        log.msg("SEND: %s" % unicode(buf, 'utf-8').encode('ascii', 'replace'))

    def connected(self, xs):
        log.msg('Connected.')

        self.xmlstream = xs

        # Log all traffic
        xs.rawDataInFn = self.rawDataIn
        xs.rawDataOutFn = self.rawDataOut

        # Need to inject our on challenge before twisted words sasl version.
        xs.addObserver('/challenge', self.challenge, 100)
        xs.addObserver('/group/welcome', self.welcome)
        xs.addObserver('/group/explore-begin', self.explore)
        xs.addObserver('/group/explore-end', self.explore_end)
        xs.addObserver('/group/subscribe-chat', self.subscribe)
        xs.addObserver('/group/subscribe-session', self.subscribe_session)
        xs.addObserver('/group/sync-begin', self.sync_begin)
        xs.addObserver('/group/sync-end', self.sync_end)
        xs.addObserver('/group/user-rejoin', self.user_rejoin)
        xs.addObserver('/group/add-node', self.add_node)
        xs.addObserver('/group/sync-segment', self.sync_segment)
        xs.addObserver('/group/sync-user', self.sync_user)
        xs.addObserver('/group/request/insert-caret', self.insert)

    def insert(self, element):
        """
        This will send an insert text command to teh associated Vim instance.

        """
        insert_node = element.firstChildElement().firstChildElement()
        offset = insert_node['pos']
        self.service.insert_vim(str(insert_node).encode('ascii', 'ignore'), int(offset),
                              self.files.keys()[0].encode('ascii', 'ignore'))


    def subscribe(self, element):
        # TODO this needs to be more robust and really ack
        self.xmlstream.send(u'<group publisher="you" name="InfDirectory">'
                            '<subscribe-ack/></group>')

    def insert_text(self, position, text):
        """
        This will insert text into the subscribed buffer.

        TODO might need to pass the buffer/sequence id in here

        Args:
            position (int): The caret position in the buffer to insert into, 0 based.
            text (string): the text to insert, often one character.

        Example: xml from gobby packet sniffing
            <group publisher="you" name="InfSession_3">
                <request user="1" time="">
                    <insert-caret pos="0">T</insert-caret>
                </request>
            </group>

        """
        self.xmlstream.send(u'<group publisher="you" name="' + self.session + '">'
                            '<request user="1" time="">'
                            '<insert-caret pos="' + str(position) + '">' + text +
                            '</insert-caret>'
                            '</request>'
                            '</group>')

    def explore_end(self, element):
        """
        Once we get the explore-end then we can send anotheer message.
        """
        self.service.new_buffer(self.files.keys()[0].encode('ascii', 'ignore'))
        file_id = self.files.values()[0]
        self.xmlstream.send(u'<group publisher="you" name="InfDirectory">'
                            '<subscribe-session seq="2" id="' + str(file_id) + '"/>'
                            '</group>')

    def subscribe_session(self, element):
        """
        This will send back an ack if we get the expected subscription confirmation
        """
        node = element.firstChildElement()
        self.session = node['group']
        self.xmlstream.send(u'<group publisher="you" name="InfDirectory">'
                            '<subscribe-ack id="' + node['id'] + '"/>'
                            '</group>')

    def sync_begin(self, element):
        """
        Handle the syncing of the file.
        """
        # TODO this should be updating the Vim buffer
        pass

    def sync_user(self, element):
        """
        This should be storing/creating data about a user but forget it for now
        """
        pass

    def sync_segment(self, element):
        """
        This is the message to update the buffer with what gobby has.
        """
        node = element.firstChildElement()
        self.service.sync_vim(str(node).encode('ascii', 'ignore'),
                              self.files.keys()[0].encode('ascii', 'ignore'))

    def sync_end(self, element):
        """
        Done with syncing send back an ack
        """
        self.xmlstream.send(u'<group publisher="you" name="' + element['name'] + '">'
                            '<sync-ack/></group>')
        self.user_join(self.session)

    def user_join(self, name):
        """
        This will join to a file or a chat group
        """
        self.xmlstream.send(u'<group publisher="you" name="' + name + '">'
                            '<user-join seq="0" name="Bob" status="active" '
                            'time="" caret="0" hue="0.28028500000000001"/>'
                            '</group>')

    def user_rejoin(self, element):
        """
        Save off the id given from infinoted
        """
        node = element.firstChildElement()
        self.user_id = node['id']

    def explore(self, element):
        """
        NOt sure if I really need to do anything here...???
        """
        pass

    def add_node(self, element):
        """
        This will add a file to the list of available files.
        """

        # There may be a better way to hook but i keep getting the root, not the element I
        # care about
        node = element.firstChildElement()
        self.files[node['name']] = node['id']

    def welcome(self, element):
        self.xmlstream.send(u'<group publisher="you" name="InfDirectory"><explore-node '
                            'seq="0" id="0" /></group>')

    def challenge(self, element):
        # Super hack not sure the exact problem but looking at RFC 2245 anonymous sasl
        # should still work with challenge response
        event, observers = self.xmlstream._getEventAndObservers('/challenge')

        # Grab priority 0 observer callbacks
        for observer in observers[0].values():
            for callback in observer.callbacks:
                if callback.im_class == SASLInitiatingInitializer:
                    if not getattr(callback.im_self.mechanism, 'getResponse', None):
                        callback.im_self.mechanism.getResponse = lambda s: s + 'hello'

    def authenticated(self, xs):
        log.msg('Authenticated.')

        presence = domish.Element((None, 'presence'))
        xs.send(presence)
