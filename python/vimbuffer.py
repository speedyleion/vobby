"""
Implements the Filebuffer for Vim interfaces


"""

import re

from twisted.python import log

from file_buffer import FileBuffer


class VimFileBuffer(FileBuffer):
    """
    This is a Vim specific :class:`FileBuffer`.  This handles mapping the
    generic FileBuffer methods through to the Vim specific instance.

    """

    def __init__(self, protocol, bufid):

        #: Used to keep track of mirror buffers from other IDEs.  This allows
        #: this buffer to tell other IDE buffers of necessary updates.
        self.buffers = []

        #: the VimBeansProtocol that created this buffer.  Used for actually
        #: sending messages to Vim instances
        self.protocol = protocol

        #: The buffer id used to communicate with Vim.  Must be unique for each
        #: buffer.
        self.bufid = bufid

    def delete(self, offset, length, user=None):
        """
        This will delete the `length` number of characters from the `offset` in
        this buffer.

        Args:
            offset (int): This is the number of characters into the buffer to
                          place `content` at.  This is a 0 based value.
                          Newlines are considered one character.  TODO: do we
                          need to worry about '\\r\\n'?

            length (int): This is the number of characters to remove from the
                          buffer.  Newlines and tabs count as one character
                          each.

        Kwargs:
            user (Unknown): This is the user who is deleting the `content`.
                            The main purpose of this is for editor interfaces
                            that support highlighting text by different users as
                            different colors.

        """
        message = '{}:remove/{} {} {}\n'.format(self.bufid,
                                                self.protocol.get_sequence_no(),
                                                offset, length)

        self.protocol.write(message)

    def insert(self, content, offset, user=None):
        """
        This will insert `content` into this buffer at `offset`.

        Args:
            content (str): This is the string to insert.  It can be one
                           character, ``a`` or it can be a full string ``Hello
                           this is my string``.

            offset (int): This is the number of characters into the buffer to
                          place `content` at.  This is a 0 based value.
                          Newlines are considered one character.  TODO: do we
                          need to worry about '\\r\\n'?

        Kwargs:
            user (Unknown): This is the user who is inserting the `content`.
                            The main purpose of this is for editor interfaces
                            that support highlighting text by different users as
                            different colors.

        """
        message = '{}:insert/{} {} "{}"\n'.format(self.bufid,
                                                  self.protocol.get_sequence_no(),
                                                  offset,
                                                  content.replace('\n', '\\n'))
        self.protocol.write(message)

    def sync(self, content):
        """
        This is usually used on initial creation/editing of a shared buffer.
        `content` will be the entire contents of the buffer.  Most
        implementations will probably remove all of the previous contents in the
        buffer and replace them with this new `content`.

        Args:
            content (str): The entire contents of the buffer.

        """
        # HACK for now just insert it all
        # import pydevd; pydevd.settrace('localhost', port=5252, stdoutToServer=True, stderrToServer=True)
        self.insert(content, 0, None)

    def process_vim_event(self, event):
        """ Handle a message from Vim

        This will parse a Vim message and disposition it appropriately

        Parameters:
            message (str): The message from Vim.  Can be any message provided it
                           was for this buffer.

        """
        event_name, args = re.split('[ =]', event, 1)

        method = getattr(self, 'event_{}'.format(event_name), None)

        if method:
            method(args)

    def event_insert(self, insert_args):
        """This will process an `insert` event from Vim

        This will notify all of :attr:`buffers` about the insertion of text by
        Vim.

        Args:
            insert_args (str): The insert argument from Vim.  Expected to be in
                               the form of '<offset> "content"'

        """
        offset, content = insert_args.split(' ', 1)

        # Strip off the leading and trailing quotes, '"'
        content = content[1:-1]
        for buf in self.buffers:
            buf.insert(int(offset), content)

    def event_remove(self, remove_args):
        """Process a 'remove' event from Vim

        This will notify all of :attr:`buffers` about the deletion of text by
        Vim.

        Args:
            remove_args (str): The remove argument from Vim.  Expected to be in
                               the form of '<offset> <length>'

        """
        offset, length = remove_args.split(' ', 1)
        for buf in self.buffers:
            buf.delete(int(offset), int(length))

    def event_keyCommand(self, command):
        """Key commands are generic commands to Vobby from Vim

        This will verify a propper key command and dispatch as necessary.  Only
        if the first word is `vobby` will this command be processed, otherwise
        it will be silently ignored.

        Args:
            command (str): The key command to process.

        """
        # First element always appears to be "0" after that strip off the quotes
        # and process as a string
        _, real_command = command.split(' ', 1)
        real_command = real_command[1:-1]
        if not real_command.startswith('vobby'):
            return

        args = real_command.split(' ')

        # dispatch to the appropriate command
        method = getattr(self, 'command_{}'.format(args[1]), None)

        log.msg('method is %s' % method)
        if method:
            method(args[2:])

    def command_hello(self, *reply):
        """
            Dummy method to try handling nbkey commands
        """

        log.msg('Hello command %s' % reply)

    def command_open(self, path):
        """
        This command will create and watch the provided buffer.
        If the buffer is already watched then this will just reset the buffer.

        Args:
            path (str): The full path to the file to open.
        """
        log.msg('Trying to open %s' % (path,))

        if len(path) != 1:
            raise TypeError("Only one file can be opened")
        self.protocol.new_buffer(path[0])
