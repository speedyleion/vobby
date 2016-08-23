"""Vim network interface

This handles communicating with Vim through the netbeans interface.

.. raw::

            +-------------------+
            |  VimBeansProtocol *----------------------*
            +---------*---------+                      |
                     / \                               |
                    /   \                              |
    +---------------*    *---------------+   +---------*-----------+
    | VimFileBuffer |    | VimFileBuffer |   | VimDirectoryManager |
    +-------+-------+    +-------+-------+   +---------*-----------+
            |                    |                     |
            |                    |                     |
    +-------+-------+    +-------+-------+   +---------*-----------+
    | IDEFileBuffer |    | IDEFileBuffer |   | IDEDirectoryManager |
    +---------------*    *---------------+   +---------*-----------+
                    \   /                              |
                     \ /                               |
            +---------*---------+                      |
            |  OtherIDEProtocol *----------------------+
            +-------------------+

"""

import re
from textwrap import dedent

from twisted.internet.protocol import Protocol, ServerFactory
from twisted.python import log

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
        #: This has two keys per buffer, except for this object.  One key is the
        #: Vim buffer number.  The other is the actual file name as retrieved
        #: from :attr:directory.
        self.buffers = {'0': self}

        self.service = service
        self.service.add_protocol(self)
        self.sequence_number = 1

        #: Get the directory structure from the service, this isn't ideal should
        #: be abstracted somehow
        self.directory = self.service.infinoted.directory['0']

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
        log.msg('Recieved data %s' % (data,))

        for line in data.splitlines():

            # For now skip the special messages
            if any(line.startswith(special) for special in
                    VIM_SPECIAL_MESSAGES):
                continue

            # Replies are usually '<sequence> [other]' so if you split these on
            # ':' then you will get the same string back
            message = line.split(':', 1)
            if len(message) > 1 and message[0].isdigit():
                self.buffers[message[0]].process_vim_event(message[1])

            # Maybe later handle Replies which use spaces but for now just
            # ignore them
            # message = re.split('[ :]', line, 1)
            # if message[0].isdigit():

    def watchFile(self, filename):
        """
        This will instruct the Vim instance to notify this of changes to the
        `filename`.

        TODO see how much this would actually be used, currently focusing on
        editing infinoted files not Vim ones.

        Args:
            filename (str): The filename of the Vim buffer to watch.  This will
                            be the filename local to the Vim instance running

        Hard coded the sequence numbers as 2 and 3.  Not quite sure yet how to
        utilize or if they need to be.

        """
        _id = str(self.bufid)
        self.buffers[_id] = VimFileBuffer(self, self.bufid)
        self.write(_id + ':putBufferNumber!2 ' + filename + '\n')
        self.write(_id + ':startDocumentListen!3\n')

        # Right now storing here.
        self.buffers[filename] = _id
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
        Create a new buffer with name `filenmae` in Vim.

        Args:
            filename (str): The filename to use.  Note that by default Vim will
                            save this to the current directory if the user saves
                            with `:w` or equivalent

        """
        if filename in self.buffers:
            return

        _id = str(self.bufid)
        self.buffers[_id] = VimFileBuffer(self, self.bufid)
        message = """\
                  {id}:create!0
                  {id}:setTitle!0 "{filename}"
                  {id}:setFullName!0 "{filename}"
                  {id}:setCaretListener!0
                  {id}:setModified!0 F
                  {id}:setContentType!0
                  {id}:startDocumentListen!0
                  """

        self.write(dedent(message.format(id=_id, filename=filename)))

        # Map the filename to the buffer number
        self.buffers[filename] = _id
        self.bufid += 1

        #

    def process_vim_event(self, event):
        """ Handle a message from Vim

        This will parse a Vim message and disposition it appropriately

        Args:
            message (string): The message from Vim.  Can be any message provided
                              it was for this buffer.

        """

        log.msg('Processing %s' % (event))
        event_name, args = re.split('[ =]', event, 1)

        method = getattr(self, 'event_{}'.format(event_name), None)

        if method:
            method(args)

    def event_startupDone(self, args):
        """Initializes the rest of the connection with Vim

        Args:
            args (string): For startup this should be 0

        """
        # Create a dummy vobby buffer
        self.new_buffer('__vobby__')

        # Feed back the directory for viewing
        self.buffers[self.buffers['__vobby__']].insert(str(self.directory), 0)


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
