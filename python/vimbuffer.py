"""
Implements the Filebuffer for Vim interfaces


"""

import re

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
            content (string): This is the string to insert.  It can be one
                              character, ``a`` or it can be a full string
                              ``Hello this is my string``.

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
            content (string): The entire contents of the buffer.

        """
        # HACK for now just insert it all
        self.insert(content, 0, None)

    def process_vim_event(self, event):
        """ Handle a message from Vim

        This will parse a Vim message and disposition it appropriately

        Parameters:
            message (string): The message from Vim.  Can be any message provided
                              it was for this buffer.

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
            insert_args (string): The insert argument from Vim.  Expected to be
                                  in the form of '<offset> "content"'

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
            remove_args (string): The remove argument from Vim.  Expected to be
                                  in the form of '<offset> <length>'

        """
        offset, length = remove_args.split(' ', 1)
        for buf in self.buffers:
            buf.delete(int(offset), int(length))
