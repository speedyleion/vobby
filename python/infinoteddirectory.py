"""
Handles the creation and communication of the shared file directory structure.


"""

import directory


class InfinotedDirectory(directory.Directory):

    """
    This will keep track of the directory/file structure of infinoted.  This is
    the same as :class:`Directory` other than the :attr:`id` will exist to
    provide a lookup for communicating back with the infinoted server.

    """
    def __init__(self, name, parent=None):
        super(InfinotedDirectory, self).__init__(name, parent)
        self.id = None


class InfinotedFile(directory.IDEFile):
    """
    This will keep track of the directory/file structure of infinoted.  This is
    the same as :class:`IDEFile` other than the :attr:`id` will exist to provide
    a lookup for communicating back with the infinoted server.

    """
    def __init__(self, name, parent=None):
        super(InfinotedFile, self, parent).__init__(name, parent)
        self.id = None
