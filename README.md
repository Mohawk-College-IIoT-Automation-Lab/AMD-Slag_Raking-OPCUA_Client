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

Any function that is defined with `async` keyword is a *coroutine function*.
A *coroutine function* is a special kind of function that can "pause" its execution (at `await`), 
then resume later where it left off, like a generator.
When a coroutine function is called a **Coroutine Object** is returned.
A **Coroutine Object** represents the function’s body or logic.

```python
import asyncio
from typing import Coroutine

async def func(param) -> str:
    print(f"Do something with {param}")
    await asyncio.sleep(param)
    return f"Result of processing {param}"

async def main():
    coroutine: Coroutine = func(1)
    task: asyncio.Task = asyncio.create_task(coroutine)
    result: str = await task
```
Logic inside `func(param)` will not be executed on line `coroutine: Coroutine = func(1)`, neither will `func(1)` be added to the event-loop's collection of jobs to be run. Merely a **Coroutine Object** will be created on this line.

### Task

Task is an entry on the event-loop's to-do list.

`func(1)` is added to the event-loop's collection of jobs to be run or is *scheduled* on this line:
    `task: asyncio.Task = asyncio.create_task(coroutine)`

### await

Translating `await work` into plain English: Countinue only when *work* is complete.

*work* can be a *coroutine* or a *task*. 
There is an important difference between `await coroutine` and `await task`, 
which I will discuss later.

The phrasing is important: The caller (coroutine) of `await work` isn't necessarely suspended. 

If work had completed at some earlier time when event-loop had had the chance to run the job, 
the calling routine just takes the result of *work* and **countinues** without ceding the control to the event-loop and waiting.

It is also improtant that the calling context continues **when** the work is complete, not *once*.
*Once* the *work* is done, the calling courtine doesn't just yank the control from whatever is running at that moment,
it goes to the end of the queue of job for the event loop to run and awaits it's turn in an orderly manner. 
*to be given* the control.

Additionally, in case *work* wasn't completed at some time before `await work` statement, 
it is not implied that work is started right at that moment, when the interpreter hits `await work`. 
In a complex program we don't know what jobs are finished, what are ready to be run, 
and what is the order of the event-loop's to-do list.
What we know and have control over is not moving forward until something is done. 
Event-loop will give control to a program that is ready to run.
If there are multiple jobs ready, the loop will select whatever task was created first
because it uses a FIFO queue under the hood. 
So, the top job of the to-do list that is ready to run will become in control.
We won't know how long it will take and what will happend in the meantime, 
the only thing we know is that the work is complete by the next time the coroutine gets the control.

For example, `await asyncio.sleep(1)` doesn't means that the coroutine will be paused for 1 second exactly.
We don't know how much time will pass until the coroutine get back the control.
We know that *at least* 1 second will elapse, but the time can be longer if event-loop's list of scheduled tasks 
cumulatively take longer than 1 second to run.

To conclude, when you write `await work` you essentially say: 
"I cannot continue this routine without the result of *work*"

#### The difference between awaiting tasks and awaiting coroutines

<Placeholder>

## Sources

- https://docs.python.org/3/howto/a-conceptual-overview-of-asyncio.html
- https://www.youtube.com/watch?v=oAkLSJNr5zY