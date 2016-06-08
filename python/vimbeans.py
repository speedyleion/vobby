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
        self.bufid = 0
        self.files = {}
        self.service = service
        self.service.add_protocol(self)
        self.sequence_number = 0

    def dataReceived(self, data):
        """
        This will parse the netbeans messages from the Vim instance and take
        appropriate action.

        """
        log.msg('Recieved data %s' % (data))

        for line in data.splitlines():

            # For now skip the special messages
            if any(line.startswith(special) for special in VIM_SPECIAL_MESSAGES):
                continue

            message = line.split(':', 1)
            if message[0].isdigit():
                self.files[message[0]].process_vim_event(message[1])

            # Maybe later handle returns which use spaces but for now just
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
        self.bufid += 1
        self.files[self.bufid] = filename
        self.transport.write(str(self.bufid) + ':putBufferNumber!2 ' + filename + '\n')
        self.transport.write(str(self.bufid) + ':startDocumentListen!3\n')

    def connectionLost(self, reason):
        """
        TODO This might need to do something probably should close connection to infinoted

        """
        log.msg('Lost connection')

    def sync(self, content, buffer_name):
        """
        Synce the `contents` of `buffer_name`
        """
        # Find the buffer
        for _file in self.files:
            if self.files[_file] == buffer_name:
                self.transport.write(str(_file) + ':insert/50 0 "' + content.replace('\n', '\\n') + '"\n')
                self.transport.write(str(_file) + ':initDone!0\n')
                break

        # Probably need a finally here...

    def delete(self, offset, length, buffer_name):
        """
        Deletes part of the buffer
        """
        for _file in self.files:
            if self.files[_file] == buffer_name:
                self.transport.write(str(_file) + ':remove/10 ' + str(offset) + ' ' +
                                     str(length) + '\n')

    def insert(self, content, offset, buffer_name):
        """
        This will insert text into the given buffer.

        Args:
            content (string): Data to insert.  Often this is one character at a time.
            offset (int): Byte offset into the buffer.
            buffer_name (string): The buffer name.

        """
        for _file in self.files:
            if self.files[_file] == buffer_name:
                self.transport.write(str(_file) + ':insert/20 ' + str(offset) + ' "' +
                                     content.replace('\n', '\\n') + '"\n')

    def get_sequence_no(self):
        """Get a Vim sequence number

        Returns: A sequence number to be used in communicating with Vim.  This
        will be more or less unique, there is some roll over but shouldn't
        collide too often.

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
        self.bufid += 1
        self.files[self.bufid] = filename
        self.transport.write(str(self.bufid) + ':create!0\n')
        self.transport.write(str(self.bufid) + ':setTitle!0 "' + filename + '"\n')
        self.transport.write(str(self.bufid) + ':setFullName!0 "' + filename + '"\n')
        self.transport.write(str(self.bufid) + ':setCaretListener!0\n')
        self.transport.write(str(self.bufid) + ':setModified!0 F\n')
        self.transport.write(str(self.bufid) + ':setContentType!0\n')
        self.transport.write(str(self.bufid) + ':startDocumentListen!0\n')


class VimBeansFactory(ServerFactory):
    """
    TODO this seems to be a twisted pattern but I don't really understand the porpoise of
    it.

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
