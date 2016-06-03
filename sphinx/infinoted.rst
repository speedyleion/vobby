Infinoted
=========

Infinoted has some documentation here, http://infinote.org/Protocol/, however
it seems a little outdated.  What follows is what has been pieced from the
outdated protocol documentation as well as by reverse engineering using
`Wireshark <https://www.wireshark.org/>`_ and snooping on Gobby to Gobby
communications.

Jabber
------

Gobby and Infinoted servers appear to use Jabber, also known as XMPP, as the main transport
mechanism.

The initial handshake of the Gobby client to the server is very similar to the
normal Jabber handshake.

.. code-block:: xml
    :caption: Client request

     <stream:stream version="1.0" xmlns="jabber:client"
     xmlns:stream="http://etherx.jabber.org/streams" to="127.0.0.1">

.. code-block:: xml
    :caption: Server reply

    <stream:stream xmlns:stream="http://etherx.jabber.org/streams"
    xmlns="jabber:client" version="1.0" from="MINE">

    <stream:features>
        <mechanisms xmlns="urn:ietf:params:xml:ns:xmpp-sasl">
            <mechanism>ANONYMOUS</mechanism>
        </mechanisms>
    </stream:features>
