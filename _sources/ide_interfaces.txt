IDE Interfaces
==============

|this_program| utilizes a generic interface for communicating between different
IDE interfaces.  This is done by implementing the :class:`FileBuffer` class.
This extra abstraction allows for possible expansion to other protocols outside
of Infinoted as well as possibly using the Vim/Netbeans implementation
elsewhere.


.. autoclass:: file_buffer.FileBuffer
    :members:
    :undoc-members:
    :show-inheritance:
