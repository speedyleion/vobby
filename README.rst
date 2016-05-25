Vobby
=====

This is a Vim plug-in which communicates with infinoted servers.

V(im)obby.

Status
------

This is very early prototype development.  The code base is ugly and it's just
there more as a proof of concept.

Getting this working for testing
--------------------------------

This currently only connects to localhost and the default ports for vim-netbeans
and infinoted.

- Start an infinoted server.
- Start Vim
- Do ":nbstart" inside of Vim
- In the repo do "./python/run.py"
- Give it a few seconds. Vim will connect ot the first buffer it finds.  Look at
the name in Vim and edit that same file in Gobby you should be able to edit
from either side.
