"""
This will test the functionality of the directory and file node logic for the
shared IDE files.

"""

from collections import namedtuple
import unittest

from directory import Directory


class TestDirectory(unittest.TestCase):

    """
    Tests the directory functionality

    :meth:`setUp` actually ends up testing the basics of making directories as
    well as making nodes

    """

    def test_walk(self):
        """
        This test the walk functionality.

        """
        ExpectedDir = namedtuple('Directory', ['dirs', 'files'])
        tree = {}
        tree['root'] = ExpectedDir(set(['sub_directory_1', 'sub_directory_2']),
                                   set(['file_1', 'file_2']))
        tree['sub_directory_1'] = ExpectedDir(set(), set())
        tree['sub_directory_2'] = ExpectedDir(set(['sub_directory_1']),
                                              set(['file_1', 'file_2']))

        viewed_dirs = []
        for root, dirs, files in self.root.walk():
            self.assertSetEqual(set([f.name for f in files]),
                                tree[root.name].files)
            self.assertSetEqual(set([directory.name for directory in dirs]),
                                tree[root.name].dirs)
            viewed_dirs.append(root.name)

        self.assertSetEqual(set(viewed_dirs), set(tree.keys()))

    def setUp(self):
        # create a basic directory structure for general testing
        #    (root)
        #       *-----file_1
        #       *-----file_2
        #       *-----sub_directory_1
        #       *-----sub_directory_2
        #                   *-----file_1
        #                   *-----file_2
        #                   *-----sub_directory_1
        self.root = Directory('root', None)

        # Use the methods to create the tree.  The first test will verify that
        # this was created correctly
        self.root.mknod('file_1')
        self.root.mknod('file_2')

        self.root.mkdir('sub_directory_1')

        self.root.mkdir('sub_directory_2')
        self.root.mknod('sub_directory_2/file_1')
        self.root.mknod('sub_directory_2/file_2')
        self.root.makedirs('sub_directory_2/sub_directory_1')
