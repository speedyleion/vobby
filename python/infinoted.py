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

from infinotedbuffer import InfinotedBuffer
from infinoteddirectory import InfinotedDirectory


class InfinotedProtocol(object):
    """
    TODO this needs to be examined, probably should be an actual
    protocol/factory setup

    """
    def __init__(self, service):
        self.finished = Deferred()

        #: This maps the infinoted id to a directory structure. '0' is always
        #: the root
        self.directory = {'0': InfinotedDirectory('')}
        self.directory['0'].id = '0'

        #: Sequences for communicating with infinoted.
        self.sequence = 1

        #: dictionary of sessionnames to InfinotedFileBuffer objects.
        self.buffers = {}
        self.service = service

        jid = JID('127.0.0.1')
        f = client.XMPPClientFactory(jid, '')
        f.addBootstrap(xmlstream.STREAM_CONNECTED_EVENT, self.connected)
        f.addBootstrap(xmlstream.STREAM_AUTHD_EVENT, self.authenticated)
        connector = SRVConnector(
            reactor, 'xmpp-client', jid.host, f, defaultPort=6523)
        connector.connect()

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
        xs.addObserver('/group/explore-begin', self.explore_begin)
        xs.addObserver('/group/explore-end', self.explore_end)
        xs.addObserver('/group/subscribe-chat', self.subscribe)
        xs.addObserver('/group/subscribe-session', self.subscribe_session)
        xs.addObserver('/group/sync-begin', self.sync_begin)
        xs.addObserver('/group/sync-end', self.sync_end)
        xs.addObserver('/group/user-rejoin', self.user_rejoin)
        xs.addObserver('/group/add-node', self.add_node)
        xs.addObserver('/group/sync-segment', self.sync_segment)
        xs.addObserver('/group/sync-user', self.sync_user)
        xs.addObserver('/group/request', self.process_buffer_request)

    def process_buffer_request(self, element):
        """ Directs the file update requests to the proper buffer instance

        Args:
            element (domish.Element): The element to update.

        Not fully understanding twisted but this seems to give more or less the
        entire element tree not just the actual request command element.
        However it makes it nice to dispatch to the correct buffer object.

        """
        self.buffers[element['name']].buffer_request(element)

    def subscribe(self, element):
        # TODO this needs to be more robust and really ack
        ack = domish.Element(('', 'subscribe-ack'))
        self.send_node(ack, element['name'])

    def explore_end(self, element):
        """
        Once we get the explore-end then we can send anotheer message.
        """
        # TODO add some kind of hold off until this finishes logic???

        # Need to broadcast that the file listing is available
        # import pydevd; pydevd.settrace('localhost', port=5252, stdoutToServer=True, stderrToServer=True)
        log.msg('Files are %s', self.directory)

    def subscribe_session(self, element):
        """
        This will send back an ack if we get the expected subscription
        confirmation

        """
        # TODO need to condition on InfDirectory vs chat, possibly???
        node = element.firstChildElement()

        # The buffer was already created so we'll just point to it from the
        # group attribute as all future updates will come via that field
        self.buffers[node['group']] = self.buffers[node['id']]
        self.buffers[node['group']].session = node['group']
        node = element.firstChildElement()

        # Send the ack
        subscribe_node = domish.Element(('', 'subscribe-ack'))
        subscribe_node['id'] = node['id']
        self.send_node(subscribe_node, 'InfDirectory')

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
        self.buffers[element['name']].event_sync(element)

    def sync_end(self, element):
        """
        Done with syncing send back an ack
        """
        ack = domish.Element(('', 'sync-ack'))
        self.send_node(ack, element['name'])
        self.user_join(element)

    def user_join(self, element):
        """
        This will join to a file or a chat group
        """
        user_attribs = {'seq': '0', 'name': 'Bob', 'status': 'active', 'time': '',
                        'caret': '0', 'hue': '0.28028500000000001'}
        user = domish.Element(('', 'user-join'), attribs=user_attribs)
        self.send_node(user, element['name'])

    def user_rejoin(self, element):
        """
        Save off the id given from infinoted
        """
        node = element.firstChildElement()
        self.user_id = node['id']

    def explore_begin(self, element):
        """
        NOt sure if I really need to do anything here...???
        """
        pass

    def add_node(self, element):
        """
        This will add a directory or file to the directory structure.
        """
        node = element.firstChildElement()

        # TODO need to handle directories
        if node['type'] == 'InfText':
            f_object = self.directory[node['parent']].mknod(node['name'])
            self.directory[node['id']] = f_object
            f_object.id = node['id']
        elif node['type'] == 'InfSubdirectory':
            # import pydevd; pydevd.settrace('localhost', port=5252, stdoutToServer=True, stderrToServer=True)
            dir_ = self.directory[node['parent']].mkdir(node['name'])
            self.directory[node['id']] = dir_
            dir_.id = node['id']

            # Need to send back an explore node for sub-directories
            self.explore(int(node['id']))
        else:
            log.msg('Non text node found: %s', node['type'])

    def explore(self, id):
        """
        This will send an explore command.  This should be given for the root
        directory, `0` and for all sub-directories.

        Args:
            id (int): The ID of the directory node to explore.
        """
        self.sequence += 1
        explore_attribs = {'seq': str(self.sequence), 'id': str(id)}
        explore = domish.Element(('', 'explore-node'), attribs=explore_attribs)
        self.send_node(explore, 'InfDirectory')

    def welcome(self, element):
        self.explore(0)

    def challenge(self, element):
        def get_response(s):
            return s + 'hello'

        # Super hack not sure the exact problem but looking at RFC 2245
        # anonymous sasl should still work with challenge response
        event, observers = self.xmlstream._getEventAndObservers('/challenge')

        # Grab priority 0 observer callbacks and monkeypatch the anonymouse
        # authentication
        for observer in observers[0].values():
            for callback in observer.callbacks:
                if callback.im_class == SASLInitiatingInitializer:
                    if not hasattr(callback.im_self.mechanism, 'getResponse'):
                        callback.im_self.mechanism.getResponse = get_response

    def authenticated(self, xs):
        # Not sure if this needs to do anything???
        pass

        # log.msg('Authenticated.')

        # presence = domish.Element((None, 'presence'))
        # xs.send(presence)

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
        self.xmlstream.send(group_node)

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

    def watchFile(self, filename, buffers=None):
        """
        This will set up being notified of changes to `filename`

        This basically sends a subscribe-session to the infinoted server

        Args:
            filename (str): The filename of the infinoted buffer to watch.

            buffers ([FileBuffer]): Any other buffers to associate with this
                                    one.

        """
        # Find the file in the directory list
        # import pydevd; pydevd.settrace('localhost', port=5252, stdoutToServer=True, stderrToServer=True)
        _id = self.directory['0'][filename].id

        self.sequence += 1
        subscribe_attribs = {'seq': str(self.sequence), 'id': _id}
        subscribe = domish.Element(('', 'subscribe-session'),
                                   attribs=subscribe_attribs)

        self.send_node(subscribe, 'InfDirectory')

        # Create the infinoted buffer
        self.buffers[_id] = InfinotedBuffer(self, None)
        # self.buffers['InfSession_' + _id] = self.buffesr[_id]

        # TODO not sure about directlly setting the attrib here
        self.buffers[_id].buffers = buffers
        for buf in buffers:
            buf.buffers.append(self.buffers[_id])
