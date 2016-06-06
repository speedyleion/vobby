"""


"""

from .file_buffer import FileBuffer


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
