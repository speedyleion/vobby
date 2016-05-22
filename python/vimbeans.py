"""
This handles communicating with Vim through the netbeans interface.
"""
from twisted.internet.protocol import Protocol, ServerFactory
from twisted.python import log


class VimBeansProtocol(Protocol):
    """
    This class implememnts the protocol of sending and recieving messages through Vims
    Netbeans interface.
    """

    def __init__(self, service):
        """
        Args:
            service (VobbyService):  This will be the object to communicate back and forth
                                     between the Vim protocol and the infinoted protocol.
        """
        self.bufid = 0
        self.files = {}
        self.service = service
        self.service.add_protocol(self)

    def dataReceived(self, data):
        """
        This will parse the netbeans messages from the Vim instance and take appropriate
        action.

        """
        log.msg('Recieved data %s' % (data))

        # TODO probably need a smarter approach, but for now hard code the decision here.

        # Handle non buffer specific commands
        if data.startswith('0'):
            data = data[2:]
            # A new Vim buffer has been opened
            if data.startswith('fileOpened'):
                self.watchFile(data.split()[1])

            return

        if data.startswith('AUTH'):
            return

        # If we got here then we are looking at a specific buffer
        for line in data.splitlines():
            sentid = int(line[0])
            command = line[2:]
            if sentid in self.files:
                # TODO we always seem to get remove and insert in the same run, so probably
                # need to optimize this some.

                # Vim uses byte offsets into buffers.  May need to handle utf-8 vs ascii...

                if command.startswith('remove'):
                    _, offset, length = command.split(' ', 2)
                    self.service.delete_gobby(int(offset), int(length), self.files[sentid])

                if command.startswith('insert'):
                    _, offset, content = command.split(' ', 2)
                    self.service.insert_gobby(content[1:-1], int(offset), self.files[sentid])

    def watchFile(self, filename):
        """
        This will instruct the Vim instance to notify this of changes to the `filename`.

        Parameters:
            filename (str): The filename of the Vim buffer to watch.  This will be the
                            filename local to the Vim instance running

        Hard coded the sequence numbers as 2 and 3.  Not quite sure yet how to utilize or if
        they need to be.

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
