"""Vim network interface

This handles communicating with Vim through the netbeans interface.

.. raw::

            *-------------------*
            |  VimBeansProtocol |
            *---------*---------*
                     / \
                    /   \
    *---------------*    *---------------*
    | VimFileBuffer |    | VimFileBuffer |
    *---------------*    *-------*-------*
            |                    |
            |                    |
    *---------------*    *---------------*
    | IDEFileBuffer |    | IDEFileBuffer |
    *---------------*    *-------*-------*
                    \   /
                     \ /
            *---------*---------*
            |  OtherIDEProtocol |
            *---------*---------*

"""
from twisted.internet.protocol import Protocol, ServerFactory
from twisted.python import log
import re

from vimbuffer import VimFileBuffer

VIM_SPECIAL_MESSAGES = ['AUTH', 'DISCONNECT', 'DETACH', 'REJECT', 'ACCEPT']


class VimBeansProtocol(Protocol):
    """
    This class implements the protocol of sending and receiving messages
    through Vims Netbeans interface.
    """

    def __init__(self, service):
        """
        Args:
            service (VobbyService):  This is the object to communicate back
                                     and forth between the Vim protocol and the
                                     VobbyService.
        """
        #: the next buffer number to use for assigning buffer numbers with Vim
        self.bufid = 1

        #: dictionary of bufid to VimFileBuffer objects.  Uses strings to
        #: represent the entries so they can be used directly from Vim.  Note
        #: '0' is this object.
        self.buffers = {}
        self.buffers['0'] = self

        self.service = service
        self.service.add_protocol(self)
        self.sequence_number = 1

    def dataReceived(self, data):
        """
        This will parse the netbeans messages from the Vim instance and take
        appropriate action.

        You'll need to look at ":help netbeans-protocol" in Vim to get the full
        documentation on these.

        http://vimdoc.sourceforge.net/htmldoc/netbeans.html#netbeans-protocol is
        an online version of the help.

        Args:
            data (str): A netbeans string message from Vim.

        """
        log.msg('Recieved data %s' % (data))

        for line in data.splitlines():

            # For now skip the special messages
            if any(line.startswith(special) for special in
                    VIM_SPECIAL_MESSAGES):
                continue

            message = line.split(':', 1)
            if message[0].isdigit():
                self.buffers[message[0]].process_vim_event(message[1])

            # Maybe later handle Replies which use spaces but for now just
            # ignore them
            # message = re.split('[ :]', line, 1)
            # if message[0].isdigit():

    def watchFile(self, filename):
        """
        This will instruct the Vim instance to notify this of changes to the
        `filename`.

        Parameters:
            filename (str): The filename of the Vim buffer to watch.  This will
                            be the filename local to the Vim instance running

        Hard coded the sequence numbers as 2 and 3.  Not quite sure yet how to
        utilize or if they need to be.

        TODO need to associate the buffer number with infinoted

        """
        self.buffers[str(self.bufid)] = VimFileBuffer(self, self.bufid)
        self.transport.write(str(self.bufid) + ':putBufferNumber!2 ' +
                             filename + '\n')

        self.transport.write(str(self.bufid) + ':startDocumentListen!3\n')
        self.bufid += 1

    def connectionLost(self, reason):
        """
        TODO This might need to do something probably should close connection to
        infinoted

        """
        log.msg('Lost connection')

    def get_sequence_no(self):
        """Get a Vim sequence number

        Returns: A sequence number to be used in communicating with Vim.  This
        will be more or less unique.

        """
        self.sequence_number += 1

        # TODO add a cap in case Vim starts getting funky with too large of a
        # value
        return self.sequence_number

    def write(self, message):
        """Writes data to Vim

        This will write out messages to the connected Vim instance.

        Args:
            message (string): The message to send to Vim

        """
        self.transport.write(message)

    def new_buffer(self, filename):
        """
        Create a new buffer with name in Vim.
        """
        self.buffers[str(self.bufid)] = VimFileBuffer(self, self.bufid)
        self.transport.write(str(self.bufid) + ':create!0\n')
        self.transport.write(str(self.bufid) + ':setTitle!0 "' +
                             filename + '"\n')
        self.transport.write(str(self.bufid) + ':setFullName!0 "' +
                             filename + '"\n')
        self.transport.write(str(self.bufid) + ':setCaretListener!0\n')
        self.transport.write(str(self.bufid) + ':setModified!0 F\n')
        self.transport.write(str(self.bufid) + ':setContentType!0\n')
        self.transport.write(str(self.bufid) + ':startDocumentListen!0\n')
        self.bufid += 1

    def process_vim_event(self, event):
        """ Handle a message from Vim

        This will parse a Vim message and disposition it appropriately

        Parameters:
            message (string): The message from Vim.  Can be any message provided
                              it was for this buffer.

        """

        log.msg('Processing %s' % (event))
        event_name, args = re.split('[ =]', event, 1)

        method = getattr(self, 'event_{}'.format(event_name), None)

        if method:
            method(args)

    def event_startupDone(self, *args):
        """Initializes the rest of the connection with Vim

        Args:
            *args (list): For startup this should be 0

        """
        # Create a dummy vobby buffer
        self.new_buffer('vobby')


class VimBeansFactory(ServerFactory):
    """
    TODO this seems to be a twisted pattern but I don't really understand the
    porpoise of it.

    """

    protocol = VimBeansProtocol

    # TODO This isn't ideal really want one service per protocol instance
    def __init__(self, service):
        self.service = service

    def buildProtocol(self, service):
        """
        This will build the protocol for the Vim protocol.
        """
        return VimBeansProtocol(self.service)
