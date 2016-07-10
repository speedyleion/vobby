"""
Generic directory interface
"""

import abc


class Directory(object):
    """
    This is an abstract class representing a directory of shared files for an
    editor.  The idea is that this class provides a generic interface for
    describing directory structure changes without having to know the nitty
    gritty details of a specific editor interface.

    TODO: create image of interface

    """
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_files(self):
        """
        This will return the shared files provided by this interface.

        """
        return
