Network Communication
=====================

|this_program| is targeted at IDE interfaces that can communicate via network
sockets.

To facilitate this communication `Twisted <https://twistedmatrix.com/trac/>`_ is
used.  The hope is that using twisted it will make this scalable and it will be
easier to add future IDE interfaces.

With the power of Twisted comes some complexity.  The following are
some suggested reading to help get a basic understanding of Twisted:

- Dave Peticolas' excellent tutorial
  http://krondo.com/an-introduction-to-asynchronous-programming-and-twisted/
- Twisted official developer guides
  http://twistedmatrix.com/documents/current/core/howto/index.html

Vobby Service
-------------

The network communication is launched as a server for Vim instances to talk to,
and as a client for an Infinoted/Gobby server.

For lack of a better term we'll call this process the "Vobby Service".

The Vobby Service is launched as a background python process which will listen
for connections from Vim instances and, depending on the desired interaction,
make connections to Infinoted servers.

The Vobby Service will be shut down when the last Vim instance closes its
connection.

.. todo:: Consider if it should be some kind of optional start-up to be able
    to stay running when passed the proper flag.
