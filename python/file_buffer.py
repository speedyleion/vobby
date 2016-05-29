"""
Generic file buffer interface
"""

import abc


class FileBuffer(object):
    """
    This is an abstract class representing a file buffer for an editor.  The
    idea is that this class provides a generic interface for describing buffer
    modifications without having to know the nitty gritty details of a specific
    editor interface.

    TODO: create image of interface

    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
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
        return

    @abc.abstractmethod
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
        return

    @abc.abstractmethod
    def sync(self, content):
        """
        This is usually used on initial creation/editing of a shared buffer.
        `content` will be the entire contents of the buffer.  Most
        implementations will probably remove all of the previous contents in the
        buffer and replace them with this new `content`.

        Args:
            content (string): The entire contents of the buffer.

        TODO may need to see about making this a list of contents so that it can
        have a user markup...???

        """
        return
