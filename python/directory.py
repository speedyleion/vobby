"""
Generic directory interface
"""


class Directory(object):
    """
    This provides a generic directory interface for listing subdirectories and
    files.

    Directory paths are always deliminated with `/`.

    """

    def __init__(self, name, parent=None):
        """Directory and its name

        Args:
            name (string): The directory name
            parent (Directory): The parent directory.  Can be None if this is
                                the root directory

        """
        self.name = name
        self.parent = parent
        self.sub_directories = []
        self.files = []

    def walk(self):
        """
        This is a similar interface to :meth:os.walk it always starts at the
        root of this directory

        """
        return

    def mkdir(self, path):
        """Create subdirectory

        Args:
            path (string): The path to make directories for.

        Raises OSError if the directory already exists

        """
        for sub_dir in self.sub_directories:
            if sub_dir.name == path:
                raise OSError('Subdirectory %s already exists' % path)

        self.sub_directories.append(Directory(path, self))

    def makedirs(self, path):
        """Recursively creates subdirectories

        Args:
            path (string): Subdirectory tree to create

        Raises OSError if the directory already exists

        """
        # This isn't ideal but more or less works for now
        sub_dirs = path.split('/', 1)
        self.mkdir(sub_dirs[0])
        if len(sub_dirs) > 1:
            self.sub_directories[-1].makedirs(sub_dirs[1])
