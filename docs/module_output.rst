Generated Module Contents
=========================

Helper functions
----------------
Each register has a set of functions for serialize and deserialize data.
These allow register fields to be manipulated using bitwise boolean operations.

The macro names are prefixed such that their definitions will not collide with
other fields of the same name.

.. data:: des_MODULE_NAME__REGISTER_NAME_f/1

    A function for deserialize a binary encoded register value.

.. data:: des_MODULE_NAME__REGISTER_NAME_[fr,fw]/1

    A function for deserialize a binary encoded register value.

    If one or more read-only + write-only fields overlap, these fields are moved
    to alternate function so that they can be accessed explicitly.

.. data:: ser_MODULE_NAME__REGISTER_NAME_f/N

    A function for serialize a record register values.

.. data:: ser_MODULE_NAME__REGISTER_NAME_[fr,fw]/N

    A function for serialize a record register value.
    
    If one or more read-only + write-only fields overlap, these fields are moved
    to alternate function so that they can be accessed explicitly.
