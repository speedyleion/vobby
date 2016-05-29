Vobby
=====

V(im)obby.

This is a Vim plug-in to enable collaborative code editing through the
`infinoted <https://gobby.github.io/>`_ protocol.  The link is actually to Gobby
but that's because it's the main client using infinoted and also usually
contains an infinoted server.

TODO insert gratuitous GIF here.

Status
------

.. warning:: Most of this documentation is how the author envisions the final
    product working.  In fact currently there is little to no actual
    implementation. Until this warning goes away the only valid documentation is
    the quick instructions in this section.

Valid Quick Start
^^^^^^^^^^^^^^^^^

The current code that exists is mainly just a proof of concept.  However if you
wish to take the plunge and test it out the following instructions should get
you there.

These steps only connect to localhost and the default ports of 6523 for
Infinoted and 3219 for Vim

- Start an infinoted server.
- Start Gobby and connect to the infinoted server. 
    - Ensure there is a file at the root of the infinoted server.
    - Type some things in the file at the root of the server.
- Start Vim
- Do ":nbstart" inside of Vim
- In the repo run the script `./python/run.py`
- Give it a few seconds. Vim will connect to the first buffer it finds.  

You should then be able to edit the file from either side.

License
-------

This is licensed using the `unlicense <http://unlicense.org>`_.  Basically do
what you will with this as long has you have fun.

Installation
------------

Simply clone this repo where it can be accessed and sourced by Vim.

Like most Vim plug-ins the suggestion is to use one of the great plug-in
managers:

- `Pathogen <https://github.com/tpope/vim-pathogen>`_
- `Vundle <https://github.com/VundleVim/Vundle.vim>`_
- `VAM <https://github.com/MarcWeber/vim-addon-manager>`_
- And many more (on channel four).

Dependencies
^^^^^^^^^^^^

- Vim compiled with python support. Doing the following in Vim 
  ``:echo has('python')`` should display a nice ``1``.
  Python 3 may work, but this author is stuck back on 2.7 so hasn't ensured
  Python 3 compatibility.

- The python package Twisted.  On most machines ``pip install twisted``.

Getting Started (Not Real Yet...)
---------------------------------

Start up Vim and run ``:VobbyConnect <ip_address>[:port]`` and this will connect
to the Infinoted server at the given ip address and port.  If the port is
omitted this will use the default of 6523.

Run ``:VobbyBrowse`` to create a vertical split showing the list of files and
directories available on the Infinoted server.  The listing should look similar
to the super awesome `nerdtree <https://github.com/scrooloose/nerdtree>`_
plug-in.

Move the cursor through the list and hit <CR>, "Enter" for those new to Vim, on
a file and that file should be opened up in the current buffer.  The file will
be populated with the contents from the Infinoted server.

Begin typing and the changes will be communicated back to the server.  If
someone else is also editing the buffer their changes will appear in the Vim
buffer as they occur.


Contributing
------------

The repo is here https://github.com/speedyleion/vobby.  Submit pull requests.

For general documentation on the internals start here,
https://speedyleion.github.io/vobby
