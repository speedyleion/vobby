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
        # TODO this may need a common retrieval method for group node and
        # request node
        root_attribs = {'publisher': 'you', 'name': self.session}
        root_node = domish.Element(('', 'group'), attribs=root_attribs)

        request_attribs = {'user': self.user_id, 'time': ''}
        request_node = domish.Element(('', 'request'), attribs=request_attribs)

        delete_attribs = {'pos': offset, 'len': length}
        delete_node = domish.Element(('', 'delete-caret'),
                                     attribs=delete_attribs)

        request_node.addChild(delete_node)
        root_node.addChild(request_node)


        self.protocol.xmlstream.send(root_node.toXml())

        # HACK need to use actual xml logic as well as genericise sending data
        # through self.protocol
        # self.protocol.xmlstream.send(u'<group publisher="you" name="' + self.session + '">'
        #                     '<request user="' + self.user_id + '" time="">'
        #                     '<delete-caret pos="' + str(offset) + '" len="' + str(length)
        #                     + '"/></request></group>')
