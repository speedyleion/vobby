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

.. code-block:: xml
    :caption: Client authentication request

    <auth xmlns="urn:ietf:params:xml:ns:xmpp-sasl" mechanism="ANONYMOUS"/>

.. code-block:: xml
    :caption: Server authentication challenge
     
     <challenge xmlns="urn:ietf:params:xml:ns:xmpp-sasl"/>

.. code-block:: xml
    :caption: Client authentication response

     <response xmlns="urn:ietf:params:xml:ns:xmpp-sasl">QXRpbGxh</response>

.. note:: Don't fully know why but twisted doesn't seem to handle anonymous
    authentication correctly.  In order to get this to work I hacked up the xmpp
    observer to have a lambda function whose :meth:getResponse was the word
    ``hello``.

        .. code-block:: python
            :caption: Hack up anonymous authentication

            def connected(self, xmlstream):
                # Need to inject our on challenge before twisted words sasl version.
                xmlstream.addObserver('/challenge', self.challenge, 100)

            def challenge(self, element):
                # Super hack not sure the exact problem but looking at RFC 2245 anonymous sasl
                # should still work with challenge response
                event, observers = self.xmlstream._getEventAndObservers('/challenge')

                # Grab priority 0 observer callbacks
                for observer in observers[0].values():
                    for callback in observer.callbacks:
                        if callback.im_class == SASLInitiatingInitializer:
                            if not getattr(callback.im_self.mechanism, 'getResponse', None):
                                callback.im_self.mechanism.getResponse = lambda s: s + 'hello'

.. code-block:: xml
    :caption: Server success

    <success xmlns="urn:ietf:params:xml:ns:xmpp-sasl"/>

.. code-block:: xml
    :caption: Client request. Not exactly sure why this is done again...

     <stream:stream version="1.0" xmlns="jabber:client"
     xmlns:stream="http://etherx.jabber.org/streams" to="127.0.0.1">

.. code-block:: xml
    :caption: Server reply

     <stream:stream xmlns:stream="http://etherx.jabber.org/streams"
     xmlns="jabber:client" version="1.0" from="MINE">

     <stream:features/>

Infinoted Handshake
-------------------

The following now are Infinoted specific messages


