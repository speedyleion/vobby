"""
This is a twisted TODO IS IT A PLUGIN OR AN APPLICATION OR WHAT? which implements the main
Vim to infinoted communication.

It will launch a server for Vim to Netbeans communication, and will connect that server to
an infinoted server for the infintoed communication.

"""

# HACK FOR NOW THIS IS A TAC FILE

from twisted.internet import reactor
from twisted.application import internet, service
from vimbeans import VimBeansFactory
from infinoted import InfinotedProtocol


class VobbyService(service.Service):
    """
    This will handle communication between the Vim protocol and the Infinoted protocol.

    The idea is that each protocol will register itself with this service when created, via
    the :meth:`add_protocol` method.  Then these protocols can then call back into this
    service with generic editing operations that each instance will know how to handle.

    """
    def __init__(self):
        self.vimbeans = None
        self.infinoted = None

    def add_protocol(self, protocol):
        """
        This will add the given `protocol` instance to this object.  If a protocol instance
        that matches the `protocol` type already exists it will be replaced.

        """
        if protocol.__class__.__name__ == 'VimBeansProtocol':
            self.vimbeans = protocol
        elif protocol.__class__.__name__ == 'InfinotedProtocol':
            self.infinoted = protocol
        else:
            raise  # Some type error

    def startService(self):
        service.Service.startService(self)
        # TODO this may need to be somewhere else.  Anyway kick off the ifinoted client.
        # and now it's super hacky
        reactor.callLater(5, self.start_infinoted)

    def start_infinoted(self):
        self.infinoted = InfinotedProtocol(self)

    def sync_vim(self, contents, buffer_name):
        """
        This will sync the `contents` with the vim buffer associated with `buffer_name`
        """
        self.vimbeans.sync(contents, buffer_name)

    def insert_vim(self, content, offset, buffer_name):
        self.vimbeans.insert(content, offset, buffer_name)

    def new_buffer(self, buffer_name):
        """
        Create a new buffer with name in Vim.
        """
        self.vimbeans.new_buffer(buffer_name)


# configuration parameters
port = 3219
iface = 'localhost'

# this will hold the services that combine to form the poetry server
top_service = service.MultiService()

vobby_service = VobbyService()
vobby_service.setServiceParent(top_service)

# the tcp service connects the factory to a listening socket. it will
# create the listening socket when it is started
factory = VimBeansFactory(vobby_service)
tcp_service = internet.TCPServer(port, factory, interface=iface)
tcp_service.setServiceParent(top_service)

application = service.Application("Vobby")

# this hooks the collection we made to the application
top_service.setServiceParent(application)
