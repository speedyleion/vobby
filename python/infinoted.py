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

from .infinotedbuffer import InfinotedBuffer

class InfinotedProtocol(object):
    """
    TODO this needs to be examined, probably should be an actual
    protocol/factory setup

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
        xs.addObserver('/group/request/delete-caret', self.delete)

    def delete(self, element):
        """ Directs the deletion request to the proper buffer to be handled

        Args:
            element (domish.Element): The element to delete.  Not fully
                                      understanding twisted but this seems to
                                      give more or less the entire element tree
                                      not just the actual delete command element

        """
        # Navigate down to the actual delete command
        delete_node = element.firstChildElement().firstChildElement()
        offset = int(delete_node['pos'])
        length = int(delete_node['len'])
        self.service.delete_vim(offset, length,
                              self.files.keys()[0].encode('ascii', 'ignore'))

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
        This will send back an ack if we get the expected subscription
        confirmation

        """
        node = element.firstChildElement()
        #TODO need to condition on InfDirectory vs chat, possibly???
        self.session = node['group']
        self.files[node['id']] = InfinotedBuffer(self, node['id'])

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

        # There may be a better way to hook but i keep getting the root, not the
        # element I care about
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

    def send_node(self, node, name):
        """Sends a node wrapped in the root `group` node

        Args:
            node (domish.Element): The node to send

            name (str): The name attribute of the group node.  Usually the
                        buffer name or InfDirectory

        """
        group_attribs = {'publisher': 'you', 'name': name}
        group_node = domish.Element(('', 'group'), attribs=group_attribs)
        group_node.addChild(node)

        # Send the actual message
        self.protocol.xmlstream.send(group_node)

    def send_request(self, request, name):
        """Sends a buffer modification request to the infinoted server

        This will build up the request structure and send the message up the
        pipe

        Args:
            request (domish.Element): The request operation element.  Something
                                      like <insert-caret> or <delete-caret>.

            name (str): The name attribute of the group node.  Usually the
                        buffer name or InfDirectory

        """
        # Create the request operation wrapper node
        request_attribs = {'user': self.user_id, 'time': ''}
        request_node = domish.Element(('', 'request'), attribs=request_attribs)

        # Add the request operation node
        request_node.addChild(request)

        self.send_node(self, request_node, name)
