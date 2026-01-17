# Notes

OPC UA is an industrial data management architecture.

Practically, OPC UA defines the data model.
OPC UA doesn't define rules for data tramission but it defines the rules for data representation.
OPC UA uses TCP/UDP for tramission, but it defines a structure for the data being transmitte

It doesn't just send a raw number like 25.5.
It sends an "Object" that tells the receiver:
"This is a temperature reading, the unit is Celsius, the high limit is 100, and it belongs to Boiler #4"

In OPC UA architecture data is logically organized into a hierarchy.
