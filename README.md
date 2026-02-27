# OPC UA

## Concepts

OPC UA is an industrial data management architecture.

Practically, OPC UA defines the data model.
OPC UA doesn't define rules for data tramission but it defines the rules for data representation.
OPC UA uses TCP/UDP for tramission, but it defines a structure for the data being transmitte

It doesn't just send a raw number like 25.5.
It sends an "Object" that tells the receiver:
"This is a temperature reading, the unit is Celsius, the high limit is 100, and it belongs to Boiler #4"

In OPC UA architecture data is logically organized into a hierarchy. Similar to a directory sctrucure.

In OPC UA everything is a node

### BrowseName

A Full Browse Name of an node is `namespace_index`:`name`

Since OPC UA architecture is hierarchical, a node can be represented as a path. For example, a Variable Node `Speed` of an Object node `Motor` in custom namespace with the index = 2 is represented as:

"0:Objects/2:Motor/2:Speed"

**0:Objects** is a standart OPC UA organizing node containing instances of all objects. All standart OPC UA nodes are located in the namespace O

**2:Motor** is Object node in namespace = 2

**2:Speed** is a Variable node. A child of the Motor Object node in the 2nd namespace

# Async

## Concepts

### Coroutine Object

Any function that is defined with `async` keyword

```python
import asyncio

async def func(param) -> str:
    print(f"Do something with {param}")
    await asyncio.sleep(param)
    return f"Result of processing {param}"
```

`func` by itself is an object of type coroutine, while `await func(param)` is the result of running the `func`, the actual `str` in the return statement

### await

`await` is used with a coroutine object to give back control to the event loop.

The `func` coroutine is a task on the scheduler's list (aka event loop). When it come the time to perform this task the following will happend:

1. f"Do something with {param}" is printed

2. The `func` task will release the control of the event loop upon hitting the `await` keyword and will be suspended until the await operation is performed (the result is avaliable)

3. When the result of the awaited operation becomes avaliable the `func` task becomes "ready".

4. The `func` courtine will wait for the scheduler to give it back the control (doesn't happend at the same time the await resource becomes avalible and depends on the list of taks)

5. `func` completes the operation by returning f"Result of processing {param}" 6. `func` courtine dissappears from the event loop list of taks
