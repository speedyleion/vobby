"""
Implements the FileBuffer interface for infinoted buffers
"""

from twisted.words.xish import domish

from file_buffer import FileBuffer


class InfinotedBuffer(FileBuffer):
    """
    This is the buffer interface for infinoted buffers
    """
    def __init__(self, protocol):
        """
        Args:
            protocol (InfinotedProtocol): The protocol to use for communicating

        """
        self.protocol = protocol
        self.bufid = subscribe_node['group']

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

        self.protocol.send_request(delete_node, self.bufid)

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
        self.protocol.send_request(insert_node, self.bufid)

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

    def buffer_request(self, element):
        """Handle buffer update request

        Args:
            element (domish.Element): The root `group` element of the request

        """
        # Second child is the actual event.  Infinoted protocol uses '-' but
        # those aren't valid method characters so convert them to '_'.
        event = element.firstChildElement().firstChildElement().name
        event.replace('-', '_')

        method = getattr(self, 'event_{}'.format(event), None)
        if method:
            method(element)

    def event_insert_caret(self, element):
        """ Process an `insert-caret` request from Infinoted

        This will notify all of :attr:`buffers` about the insertion of text as
        requested by the Infinoted server.

        Args:
            element (domish.Element): The root element of the request

        """
        insert_node = element.firstChildElement().firstChildElement()
        offset = insert_node['pos']
        content = insert_node.content  # TODO does this need ascii/vs utf8???

        for buf in self.buffers:
            buf.insert(int(offset), content)

    def event_delete_caret(self, element):
        """ Process a `delete-caret` request for Infinoted

        This will notify all of :attr:`buffers` about the deletion of text by
        the Infinoted server.

        Args:
            element (domish.Element): The root element of the request

        """
        delete_node = element.firstChildElement().firstChildElement()
        offset = delete_node['pos']
        length = delete_node['len']

        for buf in self.buffers:
            buf.delete(int(offset), int(length))

    def event_sync(self, element):
        """ This is the counter to :meth:sync

        This will notify all of :attr:`buffers` about the contents of the buffer
        as reported by the Infinoted server.

        Args:
            element (domish.Element): The root element of the request

        """
        content_node = element.firstChildElement()
        for buf in self.buffers:
            buf.sync(content_node.content)
