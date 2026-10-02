# Lab 11: Model Checking 

A model checker takes a finite description of a system and a property, then explores every reachable state to determine whether the property holds everywhere. If it finds a violation it returns the exact sequence of steps that led to it, so rare interleavings that testing would need thousands of runs to encounter are guaranteed to surface. 

There are several mature model checkers out there; for the lab we will use https://github.com/fizzbee-io/fizzbee
because it has an online playground that can be used with no installation https://fizzbee.io/play 
(it doesn't show any progress bar when running, but it does run).


## 1: Actions and State Spaces

FizzBee programs are built from actions. `Init` runs once to set up the initial state, and every other action fires repeatedly in any order until nothing is enabled.
A first simple example is that of a clock that increments every hour, modulo 12. 

```python
action Init:
  hour = 1

atomic action Tick:
  hour = (hour % 12) + 1
```

Paste this into the playground, click Run, then States Graph, and note how twelve reachable states appear in a cycle. 
Here, `atomic action` means the entire body executes as one indivisible step, so no intermediate state exists where `hour` is mid-update.

### Block modifiers

The body of an action can receive a block modifier:

- `atomic:` all statements as one step, no interleaving
- `serial:` statements in order, with yield points between them where other actions can interleave
- `oneof:` exactly one statement executes (non-deterministic choice)
- `parallel:` statements in any order, also with yield points

Without a modifier the default is `serial`, so interleaving between consecutive statements is always possible unless explicitly prevented.

```python
action Init:
  a = 0
  b = 0

action Add:
  atomic:
    a = (a + 1) % 3
    b = (b + 1) % 3
```

Run this and open States Graph. `a` and `b` always move together because `atomic` prevents interleaving. Change `atomic:` to `serial:` and the state space grows: the checker now explores states where `a` has been incremented but `b` has not yet, because another action (or another instance of Add) could fire between those two statements.

### Non-deterministic choice

The `any` keyword picks one value from a collection non-deterministically, and the checker explores all possible choices.

```python
action Init:
  value = 0
  any x in [1, 2, 3]:
    value = x
```

Run this and compare the state graph with the same code using `for` instead of `any`. With `for` the final value is always 6, but with `any` the checker explores three branches where value ends up as 1, 2, or 3.

### Exercise 1

Change the `Add` action above to use `oneof:` instead of `atomic:`. Run, open the state graph, and compare it with what `serial` and `atomic` produced.


## 2: Safety

A safety property asserts that something bad never happens. The checker verifies it against every single reachable state.

```python
always assertion AlwaysLessThan3:
  return value <= 3

action Init:
  value = 0
  any x in range(-2, 2):
    value = x

atomic action Add:
  if value < 3:
    value += 1
  else:
    value = 0
```

`any x in range(-2, 2)` means the initial value can be -2, -1, 0, or 1, so the checker branches into four parallel explorations from the start. The `always assertion` then checks `value <= 3` across all reachable states in all branches, and running it confirms it passes.

### Exercise 2

Change the assertion to `value <= 2`. Run and observe the violation trace that shows how value reaches 3 (In the "Error Graph" tab). Then change the `if` condition so the assertion passes again.

### Transition invariants

State invariants check individual states. Sometimes that is not enough, and we need to constrain which transitions between states are legal. A `transition assertion` receives the before and after state of each step.

```python
MAX_HOUR=12

action Init:
  hour = MAX_HOUR
  meridiem = "am"

atomic action HourChange:
  hour = (hour % MAX_HOUR) + 1

atomic action MeridiemChange:
  meridiem = "pm" if meridiem == "am" else "am"

transition assertion ClockBehavior(before, after):
  if before.meridiem != after.meridiem:
    return before.hour == MAX_HOUR - 1 and after.hour == MAX_HOUR
  else:
    return (before.hour == 12 and after.hour == 1) or (after.hour == before.hour + 1)
```

This models a clock with separate actions for hour change and meridiem change, where the transition assertion says meridiem can only flip when the hour goes from 11 to 12. Run it and the assertion fails because `MeridiemChange` can fire at any time independently.

### Exercise 3

Fix the model by removing the `MeridiemChange` action and putting the meridiem logic inside `HourChange` (flip meridiem when hour reaches 12). Verify the transition assertion passes.


## 3: Guard Clauses and Deadlock

FizzBee determines whether an action is enabled by a simple rule: at least one assignment must actually execute during the action's body. If an `if` branch is not taken and nothing gets assigned, the action is disabled for that state.

```python
action Init:
  switch = "OFF"

atomic action On:
  if switch != "ON":
    switch = "ON"
```

Running this produces a deadlock because once the switch is "ON" the `if` condition is false, nothing gets assigned, and the system is stuck with no enabled action.

`require` is a more explicit way to write the same thing. When the condition is false it disables the action and aborts immediately, without needing to structure the guard as an `if`.

```python
action Init:
  switch = "OFF"

atomic action On:
  require switch != "ON"
  switch = "ON"

atomic action Off:
  require switch != "OFF"
  switch = "OFF"
```

With both actions present the system alternates between ON and OFF indefinitely, and the deadlock disappears.

### Exercise 4

Model a traffic light that cycles through "red", "green", "yellow" using three actions with guard clauses (each action only fires when the light is in the correct preceding state). Verify there is no deadlock and the state graph forms a 3-state cycle.

### Exercise 5

Add a `Broken` action that can fire from any non-broken state and sets the light to "broken". Observe the deadlock. Then add a `Fix` action that transitions from "broken" back to "red" and verify the deadlock is resolved.


## 4: Liveness and Fairness

Liveness is the complement of safety. A safety property forbids bad states, and a liveness property demands that good states are eventually reached. FizzBee supports two temporal forms:

- `always eventually` asserts the system keeps returning to a given state forever, no matter how far it drifts
- `eventually always` asserts the system reaches a state and never leaves it again (stability)

```python
always eventually assertion BecomeZero:
  return value == 0

action Init:
  value = 0
  any x in range(-2, 2):
    value = x

atomic action Add:
  if value < 3:
    value += 1
  else:
    value = 0
```

Running this shows that liveness fails with a "stutter" trace, which is an execution where nothing fires after Init. `Add` is enabled but nothing forces it to execute, so the checker considers an infinite idle execution valid.

To resolve this, change `atomic action Add:` to `atomic fair action Add:`. The `fair` keyword tells the checker that an action which remains continuously enabled will eventually fire, which excludes the stutter execution and allows the liveness property to pass.

### Weak vs strong fairness

- `fair` (or `fair<weak>`): the action will eventually fire if it remains continuously enabled without interruption
- `fair<strong>`: the action will eventually fire if it is enabled infinitely often, even with interruptions in between

The distinction matters when an action's guard flickers on and off:

```python
action Init:
  status = "idle"

atomic action Process:
  if status == "idle":
    status = "working"

atomic action Finish:
  if status == "working":
    status = "idle"

atomic action Shutdown:
  if status != "working":
    status = "shutdown"
```

The system cycles between "idle" and "working". `Shutdown` can only fire from "idle", so every time `Process` fires and status becomes "working", `Shutdown` is disabled again. It is not continuously enabled, just repeatedly enabled. Weak fairness does not help here. Strong fairness is what guarantees `Shutdown` eventually fires, because it only requires the action to be enabled infinitely often, not continuously.

### Exercise 6

Add `always eventually assertion SafelyShutdown: return status == "shutdown"` to the model above. Add `fair` to `Shutdown` and verify it fails. Then change to `fair<strong>` and verify it passes.

### Exercise 7

Model the following request processing system and verify liveness:

```python
always eventually assertion SafelyShutdown:
  return status == "shutdown"

always eventually assertion Working:
  return status == "working"

action Init:
  status = "idle"

atomic fair<strong> action Start:
  if status == "idle":
    status = "working"

atomic fair action Finish:
  if status == "working":
    status = "idle"

atomic fair<strong> action Shutdown:
  if status not in ["working", "failed"]:
    status = "shutdown"

atomic action Fail:
  if status != "shutdown":
    status = "failed"

atomic fair action Fix:
  if status == "failed":
    status = "idle"

atomic fair action Restart:
  if status == "shutdown":
    status = "idle"
```

Run this and verify both liveness properties pass. Then experiment with breaking the model:

- Remove `fair<strong>` from `Start` and make it just `fair`. Run. Does `Working` still hold?
- Restore `Start` but remove `fair` from `Fix`. The system can now get stuck in "failed" forever because nothing forces `Fix` to fire.
- Make `Fail` fair (`atomic fair action Fail`). Run and look at the state graph. What does this imply about the system's behavior?
- Add `eventually always assertion StayShutdown: return status == "shutdown"`. This asks whether the system eventually shuts down and stays down. Run and observe why it cannot hold.
