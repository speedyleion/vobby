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
        #: buffer. Stored as a string so it doesn't need to be converted on each
        #: write
        self.bufid = str(bufid)

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
        self.protocol.write(self.bufid + ':remove


