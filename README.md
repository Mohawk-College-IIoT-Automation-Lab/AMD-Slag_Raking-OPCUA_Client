# Concepts

OPC UA is an industrial data management architecture.

Practically, OPC UA defines the data model.
OPC UA doesn't define rules for data tramission but it defines the rules for data representation.
OPC UA uses TCP/UDP for tramission, but it defines a structure for the data being transmitte

It doesn't just send a raw number like 25.5.
It sends an "Object" that tells the receiver:
"This is a temperature reading, the unit is Celsius, the high limit is 100, and it belongs to Boiler #4"

In OPC UA architecture data is logically organized into a hierarchy. Similar to a directory sctrucure.

In OPC UA everything is a node

## BrowseName

A Full Browse Name of an node is `namespace_index`:`name`

Since OPC UA architecture is hierarchical, a node can be represented as a path. For example, a Variable Node `Speed` of an Object node `Motor` in custom namespace with the index = 2 is represented as:

"0:Objects/2:Motor/2:Speed"

**0:Objects** is a standart OPC UA organizing node containing instances of all objects. All standart OPC UA nodes are located in the namespace O

**2:Motor** is Object node in namespace = 2

**2:Speed** is a Variable node. A child of the Motor Object node in the 2nd namespace
