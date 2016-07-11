"""
This will test the functionality of the directory and file node logic for the
shared IDE files.

"""

import unittest

from directory import Directory


class TestDirectory(unittest.TestCase):

    """
    Tests the directory functionality

    """

    def test_basic_dir(self):
        for root, dirs, files in self.root.walk():
            self.assertEquals(root.name, 'root')
            self.assertSetEqual(set([f.name for f in files]),
                                set(['file_1', 'file_2']))
            self.assertSetEqual(set([directory.name for directory in dirs]),
                                set(['sub_directory_1', 'sub_directory_2']))

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
