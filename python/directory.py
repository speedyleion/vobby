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
            name (str): The directory name
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
            for root, dirs, files in sub.walk():
                yield (root, dirs, files)

    def mkdir(self, path):
        """Create subdirectory

        Args:
            path (str): The path to make directories for.

        Raises OSError if the directory already exists

        """
        if path in self.sub_directories or path in self.files:
            raise OSError("Cannot create a file when that file already exists: "
                          "'%s'" % path)

        self.sub_directories[path] = Directory(path, self)

        # This deviates, but I need/want some way to access the file object
        # right away
        return self.sub_directories[path]

    def makedirs(self, path):
        """Recursively creates subdirectories

        Args:
            path (str): Subdirectory tree to create

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
            path (str): The file to create

        """
        # TODO rework this really this should probably be sub_dir.mknod and then
        # when it gets to nothing that does self.files[fname]...
        sub_dirs = path.rsplit('/', 1)
        if len(sub_dirs) > 1:
            fname = sub_dirs[1]
            sub_dir = self._get_sub_directory(sub_dirs[0])
        else:
            fname = path
            sub_dir = self
        sub_dir.files[fname] = IDEFile(fname, sub_dir)

        # This deviates, but I need/want some way to access the file object
        # right away
        return sub_dir.files[fname]

    def remove(self, path):
        """Remove a file

        Args:
            path (str): File to remove

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
            path (str): Directory to remove

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

    def __str__(self):
        # TODO would really like this to provide an output similar to the "tree"
        # command
        # import pydevd; pydevd.settrace('localhost', port=5252, stdoutToServer=True, stderrToServer=True)
        indent = 4
        prefix = ' ' * indent + '*' + '-' * indent
        filenames = []
        for f in self.files:
            filenames.append(prefix + f)

        filenames.append('')
        tree = self.name + '\n' + '\n'.join(filenames)

        for d in self.sub_directories:
            dir_ = str(d).split()
            dir_ = '\n    '.join(dir_)
            tree += prefix + dir_

        return tree

    def __getitem__(self, key):
        """
        This allows for looking up files and directories by dictionary style
        strings

        """
        import pydevd; pydevd.settrace('localhost', port=5252, stdoutToServer=True, stderrToServer=True)
        sub_dirs = key.split('/', 1)
        if len(sub_dirs) > 1:
            try:
                return self.sub_directories[sub_dirs[0]][sub_dirs[1]]
            except KeyError:
                raise KeyError(key)

        try:
            return self.sub_directories[sub_dirs[0]]
        except KeyError:
            return self.files[sub_dirs[0]]

    def __contains__(self, path):
        """
        This will check if a given path is inside of the directory.
        The path has to match from the root so if the directory has.

        .. warning:: This doesn't handle '/blah' right now

        >>> root = Directory()
        >>> root.makedirs('foo/bar/baz/bam')
        >>>'foo/bar' in root
        True
        >>> 'bar/baz' in root
        False

        Args:
            path (str): The path to look for.

        """
        # TODO need to make a dictionary like getter and use that.
        sub_dirs = path.split('/', 1)
        if len(sub_dirs) > 1:
            # Try to get to the parent
            try:
                return sub_dirs[1] in self.sub_directories[sub_dirs[0]]
            except KeyError:
                return False

        # It could be a file or a sub-directory
        return sub_dirs[0] in self.sub_directories or sub_dirs[0] in self.files

    def _get_sub_directory(self, path):
        """
        This will return a nested sub directory. Or self if path is None

        Args:
            path (str): The path to get.

        Returns:
            Directory

        Example:
            self._get_sub_directory('sub_1/sub_2/sub_3')
            would return the sub_3 directory instance.

        Raises:
            OSError if the directory doesn't exist


        """
        if not path:
            return self

        sub_dirs = path.split('/', 1)
        try:
            if len(sub_dirs) > 1:
                return self.sub_directories[sub_dirs[0]].\
                        _get_sub_directory(sub_dirs[1])
            else:
                return self.sub_directories[sub_dirs[0]]
        except KeyError:
            raise OSError("Subdirectory %s doesn't exist" % (sub_dirs[0],))


class IDEFile(object):
    """
    A basic file object.
    """

    def __init__(self, name, parent):
        """Directory and its name

        Args:
            name (str): The file name
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
