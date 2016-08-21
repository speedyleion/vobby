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

.. code-block:: xml
    :caption: A second server message

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
    authentication correctly.  In order to get this to work I monkey patched the
    xmpp observer to have a lambda function whose :meth:`getResponse` was the
    word ``hello``.

        .. code-block:: python
            :caption: Monkeypatch anonymous authentication

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
    :caption: Server reply (shorter than before)

     <stream:stream xmlns:stream="http://etherx.jabber.org/streams"
     xmlns="jabber:client" version="1.0" from="MINE">

     <stream:features/>

Infinoted Handshake
-------------------

The following now are Infinoted specific messages.

It looks as if the first thing after the xmpp handshake is the Infinoted server
provides a "welcome" message with the permissions.

.. code-block:: xml
    :caption: Server welcome message

     <group name="InfDirectory">
        <welcome protocol-version="1.1" sequence-id="1">
            <note-plugins>
                <note-plugin type="InfText"/>
            </note-plugins>
            <acl>
                <sheet id="default" can-add-subdirectory="yes"
                can-add-document="yes" can-sync-in="yes" can-remove-node="yes"
                can-explore-node="yes" can-subscribe-chat="yes"
                can-subscribe-session="yes" can-join-user="yes"
                can-query-account-list="no" can-create-account="no"
                can-override-account="no" can-remove-account="no"
                can-query-acl="no" can-set-acl="no"/>
            </acl>
        </welcome>
    </group>

The Gobby clients would then send an explore node to list the files and
directories available on the server.  

.. note:: The explore needs to be done for every subdirectory.

Currently not certain on the publisher attribute...

.. code-block:: xml
    :caption: Client explore request

    <group publisher="you" name="InfDirectory">
        <explore-node seq="0" id="0"/>
    </group>

The Infinoted server would reply back with a header specifying how many messages
are to follow.  In the following case there were three files on the Infinoted
server.

Looking at http://infinote.org/protocol/directory/ it seems that the seq of
`1/0` is a combination of client id from the server welcome message, and the
explore request `seq` attribute. So it's `sequence-id/seq`.

.. code-block:: xml
    :caption: Server explore header

    <group name="InfDirectory">
        <explore-begin total="3" seq="1/0"/>
    </group>

.. code-block:: xml
    :caption: First file

    <group name="InfDirectory">
        <add-node id="3" parent="0" name="test_gobby" type="InfText" seq="1/0"/>
    </group>

My derivation of the attributes on `add-node`:

id
    The numerical value to reference this node by.

parent
    If this node is in a subdirectory this would be the numerical value of the
    parent node.

name
    The name of the file as seen on Gobby clients.

type
    The type of node `InfText` is a normal text document.
    
    It appears that `InfSubDirectory` is a subdirectory instance.
    While `InfDirectory` appears to be the root.

seq
    Believe it to be ``<client_id>/<request_seq>``.

A couple more file nodes that were sent.  Their names are *mine* and *yes*.
Sorry not very original in my testing.

.. code-block:: xml
    :caption: Second file

    <group name="InfDirectory">
        <add-node id="2" parent="0" name="mine" type="InfText" seq="1/0"/>
    </group>

.. code-block:: xml
    :caption: Third file
    
    <group name="InfDirectory">
        <add-node id="1" parent="0" name="yes" type="InfText" seq="1/0"/>
    </group>

Finally the server *closes* the end of exploring.

.. code-block:: xml
    :caption: End of explore

    <group name="InfDirectory">
        <explore-end seq="1/0"/>
    </group>

User Registration
^^^^^^^^^^^^^^^^^

TODO 

File Subscribing
^^^^^^^^^^^^^^^^

Once a list of the files has been sent to the client the client can request to
subscribe to changes to the files.

.. code-block:: xml
    :caption: Subscribe to a File

    <group publisher="you" name="InfDirectory">
        <subscribe-session seq="2" id="3"/>
    </group>

My derivation of the attributes on `subscribe-session` request:

id
    The ``id`` from a file sent in the `explore-begin` message.

seq
    Believe it to be the same as the `explore-node` `seq`.  Basically a more or
    less incrementing number to differentiate subsequent requests and their
    replies.

.. code-block:: xml
    :caption: Server reply

    <group name="InfDirectory">
        <subscribe-session group="InfSession_3" method="central" id="3"
        seq="1/2"/>
    </group>

My derivation of the attributes on `subscribe-session` reply:

group
    This string will be used for communicating file contents and changes.

id
    The ``id`` from a file sent in the `explore-begin` message.

method
    NOT SURE

seq
    Believe it to be ``<client_id>/<request_seq>``.

The client then sends a subscription Ack.  It looks like the only thing is the
new `subscribe-ack` node as well as the `id` of the requested file.

.. code-block:: xml
    :caption: Subscription Ack

    <group publisher="you" name="InfDirectory">
        <subscribe-ack id="3"/>
    </group>

The server will then begin syncing the file contents to the client.

.. code-block:: xml
    :caption: File syncronization

    <group name="InfSession_3">
        <sync-begin num-messages="1"/>
    </group>

Notice how the `name` attribute of the `group` node is the same as the `group`
attribute for the `subscribe-session` reply.

I didn't do thorough testing to know if this was simply a concatenation of
``InfSession_`` and the `id` for the buffer or if there is more logic to it.

The users who have modified the file will next be sent.  

.. todo:: This was an empty buffer, may need a better example

.. code-block:: xml
    :caption: Sync User data

    <group name="InfSession_3">
        <sync-user id="1" name="Tom" status="unavailable" time="" caret="0"
        selection="0" hue="0.28028500000000001"/>
    </group>

My derivation of the attributes on `sync-user` reply:

id
    The client id of the user.  

name
    Name of the user

status
    Not sure what else is available

caret
    The position of the users cursor

selection
    Not sure exactly guessing it goes "backward" from the current cursor
    position??

hue
    The color used to represent the user in gobby editors.

The client will then send back a sync ack.

.. code-block:: xml
    :caption: Sync Ack

    <group publisher="you" name="InfSession_3">
        <sync-ack/>
    </group>

File Edition
^^^^^^^^^^^^

The main commands for editing a file are insert and delete.

.. code-block:: xml
    :caption: Insert command

    <group publisher="you" name="InfSession_3">
        <request user="1" time="">
            <insert-caret pos="119">s</insert-caret>
        </request>
    </group>

Here you can see that `InfSession_3` is the file to modify.  The request node
contains the user id that was sent with INSERT LINK HERE.  Time appears to be
empty not sure why or what it's supposed to represent.  `delete-caret` is the
actual delete request node.  It has:

pos
    The char offset into the buffer to start deleting from.  IS THIS 0 or 1
    BASED?

The contents of the `insert-caret` node are the contents to insert.  Usually the
network messages are fast so when typing this is only one character at a time.
However if you paste a block of text like `hello` then it would be
            ``<insert-caret pos="119">hello</insert-caret>``

.. code-block:: xml
    :caption: Delete command

    <group publisher="you" name="InfSession_3">
        <request user="1" time="">
            <delete-caret pos="23" len="1"/>
        </request>
    </group>

Here you can see that `InfSession_3` is the file to modify.  The request node
contains the user id that was sent with INSERT LINK HERE.  Time appears to be
empty not sure why or what it's supposed to represent.  `delete-caret` is the
actual delete request node.  It has:

pos
    The char offset into the buffer to start deleting from.  IS THIS 0 or 1
    BASED?

len
    The number of characters to delete.  HOW DOES THIS HANDLE LINE ENDINGS? "\n"
    vs "\r\n"?


