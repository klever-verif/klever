### Feature: Channels

This feature introduces **channels** as the primary communication mechanism between transactors in the verification environment.

#### Context

A verification environment consists of multiple **transactors** that either send transactions, receive transactions, or do both. Typical examples include drivers, monitors, and higher-level testbench components. These transactors must exchange transactions in well-defined, flexible, and comprehensible ways.

#### Problem Statement

Traditional TLM-style communication, as seen in UVM and Python UVM-like implementations, relies on ports, exports, imports, and multiple specialized port types (analysis ports, blocking/non-blocking ports, etc.). While functional, this model is:

* Conceptually heavy and verbose
* Difficult to reason about without prior deep familiarity
* Prone to wiring mistakes and unclear dataflow
* High in cognitive overhead due to indirection and implicit propagation rules

Although the model can be learned, it does not scale well in terms of clarity or developer ergonomics, especially in a modern Python-first framework.

#### Proposed Solution

Introduce **channels** as a unified, explicit, and minimal abstraction for communication between transactors.

Channels are inspired by:

* Python **Trio** channels
* **Go** channels
* Similar message-passing primitives in **Rust**

The core idea is to model communication explicitly as message passing over well-defined endpoints, instead of implicit port graphs.

---

## 1. Conceptual Model

### 1.1 Asynchronous channels between tasks and transactors

Channels are **asynchronous** communication primitives used to exchange transactions between concurrent tasks and transactors.

### 1.2 Unidirectional link with two endpoint types

Each channel is a **unidirectional communication link** with exactly two endpoint roles:

* **Sender endpoint** (`TX`)
* **Receiver endpoint** (`RX`)

The channel object itself is considered an internal implementation detail. Users interact only through endpoints.

This mirrors common OS patterns (files/sockets): users work with **handles/descriptors**, not the underlying resource object.

### 1.3 Multiplicity via clonable endpoints

A channel may effectively have:

* One sender and one receiver
* Multiple senders and one receiver (MP-SC)
* One sender and multiple receivers (SP-MC)
* Multiple senders and multiple receivers (MP-MC)

Multiplicity is achieved by making endpoints **clonable**:

* Cloning a sender creates an additional producer into the same channel.
* Cloning a receiver creates an additional consumer from the same channel.

This enables flexible construction of communication topologies without introducing separate channel types per topology.

---

## 2. Construction and Wiring

### 2.1 Endpoints can only be created via channel creation

Endpoints cannot be instantiated independently. They are produced only as part of channel creation.

A single construction entry point exists:

* `create(...) -> (rx, tx)` (or `(receiver, sender)`; naming is interchangeable)

The `create` call takes attributes that define channel semantics (buffering/broadcast/rendezvous, capacity, copy-on-send, etc.) and returns endpoints.

### 2.2 Expected creation phase: connect/wiring layer

Channels are expected to be created during the environment wiring stage:

* During a **Connect** phase (or equivalent)
* At environment/top-level composition time where all components are instantiated and wired

Endpoints are then passed explicitly into transactor constructors or task entry points.

---

## 3. Implementation Substrate

Channels are implemented on top of **cocotb primitives**:

* **Buffered** and **broadcast** channels are backed by `Queue`
* **Rendezvous** channels are implemented using cocotb **Events** and **Tasks**

The abstraction layer exposes a uniform endpoint API independent of the underlying cocotb mechanism.

---

## 4. Endpoint API

### 4.1 Receiver endpoint (`RX`)

#### Blocking receive

* `receive()` is blocking.
* Error behavior:

  * Raises `DisconnectedError` if no sender endpoints are currently connected/alive.
  * Raises `ClosedError` if `receive()` is called on a closed receiver endpoint.

#### “Wait for senders” receive

* `receive_eventually()` waits for a value and, if needed, waits for sender endpoints to appear.
* Intended behavior: if a receive attempt results in disconnection, the receiver waits until a sender is connected and retries.

#### Iteration support

The receiver is iterable, enabling idioms like:

* `async for item in rx: ...`

Iteration continues while the channel has active sender endpoints (i.e., iteration ends only when there are no senders left, according to the channel’s liveness model).

#### Lifecycle and utility

* `clone()` to create an additional consumer for the same channel
* `close()` to explicitly close this endpoint
* Ability to access/derive the opposite endpoint:

  * `tx()` or `sender()` extracted from the receiver, enabling reply/back-channel patterns without explicitly storing both ends everywhere

### 4.2 Sender endpoint (`TX`)

Sender API mirrors the receiver where meaningful.

#### Blocking send

* `send(item)` is blocking.
* Error behavior:

  * Raises `DisconnectedError` if no receiver endpoints are currently connected/alive.
  * Raises `ClosedError` if `send()` is called on a closed sender endpoint.

#### “Wait for receivers” send

* `send_eventually(item)` waits until receivers exist and then delivers the item.
* Intended behavior: if a send attempt results in disconnection, the sender waits for receivers to connect and retries.

#### Lifecycle and utility

* `clone()` to create an additional producer for the same channel
* `close()` to explicitly close this endpoint
* Ability to access/derive the opposite endpoint:

  * `rx()` or `receiver()` extracted from the sender, enabling symmetric wiring patterns

#### Non-iterable

The sender endpoint is not iterable.

---

## 5. Message Semantics

### 5.1 Copy-on-send option

Channels support an option analogous to **copy-on-send**:

* When enabled, the sender delivers a copy of the item to receivers.
* Primary use: preserve transaction immutability / prevent accidental shared mutation.
* Particularly important for broadcast channels, but may be enabled for other channel types as well.

---

## 6. Communication Styles

Channels cover the primary verification communication styles:

* **Buffered exchange** (Queue-backed)
* **Broadcast** (Queue-backed fanout)
* **Rendezvous** (Event/Task-backed synchronous handoff)

Combined with endpoint cloning, these cover the required topology space:
MP-MC, MP-SC, SP-MC, SP-SC.

---

## 7. Design Goals

* Provide a **simple and explicit** mental model for transactor communication
* Reduce cognitive load compared to TLM-style ports
* Make dataflow obvious from endpoint wiring
* Enable flexible composition without specialized port taxonomies
* Align with modern concurrency and message-passing paradigms
* Fit verification realities: long-lived infrastructure, dynamic attachment, explicit closure, and minimal implicit shutdown behavior
