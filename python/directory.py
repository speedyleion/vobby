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
        self.sub_directories = {}
        self.files = {}

    def walk(self):
        """
        This is a similar interface to :meth:os.walk it always starts at the
        root of this directory

        """
        # First yield ourself
        yield self, self.sub_directories.itervalues(), self.files.itervalues()

        # Now iterate through all subdirectories
        for sub in self.sub_directories.itervalues():
            yield sub.walk()

    def mkdir(self, path):
        """Create subdirectory

        Args:
            path (string): The path to make directories for.

        Raises OSError if the directory already exists

        """
        if path in self.sub_directories or path in self.files:
            raise OSError("Cannot create a file when that file already exists: "
                          "'%s'" % path)

        self.sub_directories[path] = Directory(path, self)

    def makedirs(self, path):
        """Recursively creates subdirectories

        Args:
            path (string): Subdirectory tree to create

        Raises OSError if the directory already exists

        """
        # This isn't ideal in that it can create part of the tree and fail out,
        # leaving part of the tree there.
        sub_dirs = path.split('/', 1)
        if len(sub_dirs) > 1:
            # Try to make parent directory and ignore OSError if it already
            # exists
            try:
                self.mkdir(sub_dirs[0])
            except OSError:
                pass

            self.sub_directories[sub_dirs[0]].makedirs(sub_dirs[1])

        else:
            self.mkdir(path)

    def mknod(self, path):
        """Create a filename "node"

        Args:
            path (string): The file to create

        """
        # TODO should probably handle path that is 'a/b/filename.x'
        self.files[path] = IDEFile(path, self)

    def remove(self, path):
        """Remove a file

        Args:
            path (string): File to remove

        Raises OSError if path isn't a file

        """
        # TODO add some error handling
        for f in self.files:
            if f.name == path:
                self.files.remove(f)
                break

    def rmdir(self, path):
        """ Remove directory

        Args:
            path (string): Directory to remove

        Raises OSError if the directory isn't empty

        """
        for sub_dir in self.sub_directories:
            if sub_dir.name == path:
                self.sub_directories.remove(sub_dir)
                break

    def is_dir(self):
        return True

    def is_file(self):
        return False


class IDEFile(object):
    """
    A basic file object.
    """

    def __init__(self, name, parent):
        """Directory and its name

        Args:
            name (string): The file name
            parent (Directory): The parent directory.

        """
        if not parent:
            raise OSError('Files always need a root directory')
        self.name = name
        self.parent = parent

    def is_dir(self):
        return False

    def is_file(self):
        return True
