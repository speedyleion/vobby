"""
Implements the FileBuffer interface for infinoted buffers
"""

from twisted.words.xish import domish

from .file_buffer import FileBuffer

class InfinotedBuffer(FileBuffer):
    """
    This is the buffer interface for infinoted buffers
    """
    def __init__(self, protocol, id):
        """
        Parameters:
            protocol (InfinotedProtocol): The protocol to use for communicating

            id (string): The file id from the infinoted server.

        """
        self.protocol = protocol
        self.id = id

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
        delete_attribs = {'pos': offset, 'len': length}
        delete_node = domish.Element(('', 'delete-caret'),
                                     attribs=delete_attribs)

        self.protocol.send_request(delete_node)

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
        insert_node = domish.Element(('', 'insert-caret'))
        insert_node['pos'] = offset  # TODO check the int to string stuff here??
        insert_node.addContent(content)
        self.protocol.send_request(insert_node)

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
