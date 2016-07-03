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

        self._send_request(delete_node)

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
        self._send_request(insert_node)

    def _send_request(self,  request):
        """Sends a buffer modification request to the infinoted server

        This will build up the request structure and send the message up the
        pipe

        Args:
            request (domish.Element): The request operation element.  Something
                                      like <insert-caret> or <delete-caret>.

        """
        # Create the request operation wrapper nodes
        root_attribs = {'publisher': 'you', 'name': self.session}
        root_node = domish.Element(('', 'group'), attribs=root_attribs)

        request_attribs = {'user': self.user_id, 'time': ''}
        request_node = domish.Element(('', 'request'), attribs=request_attribs)
        root_node.addChild(request_node)

        # Add the request operation node
        request_node.addChild(request)

        # Send the actual message
        self.protocol.xmlstream.send(root_node.toXml())
