"""Asynchronous channels for inter-task communication.

Every channel has two kinds of endpoints: sender and receiver.
So, basically it is a unidirectional communication link.
Channel is not restricted to a single sender and receiver,
it can be used to connect multiple endpoints in any combination.
So, any of communication patterns is allowed: SPSC, MPSC, MPMC, etc.

Both endpoints are constructed together with an underlying channel using `create` function.
Endpoints can be cloned using `clone` method to create multiple endpoints bound to the same channel.
It is also possible to derive an endpoint of the opposite type using `derive_sender` or `derive_receiver` methods.

Channel can be in three modes:

* Broadcast mode - every sender sends the item to all receivers (each gets a copy if `copy_on_send` is enabled)
* Work queue mode - classic work queue pattern, every sender sends the item to a single receiver
* Rendezvous mode - zero-capacity channel where sender blocks until receiver is ready (and vice versa)

Channel can have a capacity, which limits the number of items that can be buffered in the channel.
If the channel is full, the sender will block until the channel is ready to receive more items.
If the channel is empty, the receiver will block until the channel is ready to provide more items.
Capacity of 0 creates a rendezvous channel. Broadcast mode always uses unlimited capacity.

Channel creation can be restricted to single producer and/or single consumer using the corresponding flags.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections import deque
from typing import TYPE_CHECKING, Any, Self, TypeVar, final

if TYPE_CHECKING:
    from types import TracebackType

from cocotb.queue import Queue
from cocotb.task import Task, current_task
from cocotb.triggers import Event, Lock

from .types import SupportsCopy

# Invariant generic type
T = TypeVar("T")

# The type produced by receiver.
# Covariant means Receiver[Derived] can be passed to someone expecting Receiver[Base].
ReceiverType_co = TypeVar("ReceiverType_co", covariant=True)

# The type accepted by producer.
# Contravariant means Sender[Base] can be passed to someone expecting Sender[Derived].
SenderType_contra = TypeVar("SenderType_contra", contravariant=True)


class DisconnectedError(Exception):
    """Raised when there are no open endpoints of the opposite type and operation cannot succeed."""


class ClosedError(Exception):
    """Raised on attempt to operate with a closed endpoint."""


class _Channel[T](ABC):
    """Base class for channels.

    Channel itself does not use a lock.
    However, methods that may modify the state of the channel, should be called with the channel locked.
    """

    def __init__(
        self,
        copy_on_send: bool,
        only_single_producer: bool,
        only_single_consumer: bool,
    ) -> None:
        """Initialize the channel."""
        self._copy_on_send = copy_on_send
        self._only_single_producer = only_single_producer
        self._only_single_consumer = only_single_consumer

        self._open_senders = 0
        self._open_receivers = 0

        self.lock = Lock()
        self.senders_available = Event()
        self.receivers_available = Event()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} @{id(self):#x}>"

    def add_sender(self, _endpoint: _Endpoint[T]) -> None:
        """Add a sender to the channel."""
        self._open_senders += 1
        self.senders_available.set()

    def add_receiver(self, _endpoint: _Endpoint[T]) -> None:
        """Add a receiver to the channel."""
        self._open_receivers += 1
        self.receivers_available.set()

    def remove_sender(self, _endpoint: _Endpoint[T]) -> None:
        """Remove a sender from the channel."""
        self._open_senders -= 1
        if self._open_senders == 0:
            self.senders_available.clear()

    def remove_receiver(self, _endpoint: _Endpoint[T]) -> None:
        """Remove a receiver from the channel."""
        self._open_receivers -= 1
        if self._open_receivers == 0:
            self.receivers_available.clear()

    @property
    def copy_on_send(self) -> bool:
        """Copy on send setting."""
        return self._copy_on_send

    @property
    def only_single_producer(self) -> bool:
        """Only single producer setting."""
        return self._only_single_producer

    @property
    def only_single_consumer(self) -> bool:
        """Only single consumer setting."""
        return self._only_single_consumer

    @abstractmethod
    async def send(self, _endpoint: _Endpoint[T], value: T) -> None:
        """Send a value to the channel."""
        raise NotImplementedError("send is not implemented")

    @abstractmethod
    async def receive(self, _endpoint: _Endpoint[T]) -> T:
        """Receive a value from the channel."""
        raise NotImplementedError("receive is not implemented")


class _QueueChannel(_Channel[T]):
    """Channel that is used to communicate in a classic work/shared queue pattern.

    There is a single queue for all receivers. All receivers consume from the same queue concurrently.
    Queue has a fixed capacity (positive integer).

    When the channel is full, the sender will block until the channel is ready to receive more items.
    When the channel is empty, the receiver will block until the channel is ready to provide more items.
    """

    def __init__(self, capacity: int, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._capacity = capacity
        if capacity < 1:
            raise ValueError("Capacity must be a positive integer")
        self._buffer = Queue[T](maxsize=capacity)

    @property
    def capacity(self) -> int:
        """Capacity of the channel."""
        return self._capacity

    async def send(self, _endpoint: _Endpoint[T], value: T) -> None:
        """Send a value to the channel, blocking if necessary."""
        if self.copy_on_send:
            if not isinstance(value, SupportsCopy):
                raise TypeError("Sent value has to implement SupportsCopy protocol to satisfy copy_on_send setting")
            value = value.copy()

        if not self.receivers_available.is_set():
            raise DisconnectedError("Cannot send when there are no open receivers")

        await self._buffer.put(value)

    async def receive(self, _endpoint: _Endpoint[T]) -> T:
        """Receive a value from the channel."""
        if not self.senders_available.is_set():
            raise DisconnectedError("Cannot receive when there are no open senders")

        return await self._buffer.get()


class _BroadcastChannel(_Channel[T]):
    """Channel that is used to communicate in a broadcast pattern.

    There are separate queues for each receiver. And each receiver consumes from its own queue.
    So, every receiver gets the same sent value (copy if needed) independently.

    Capacity of queues is unlimited to avoid backpressure from receivers.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._queues: dict[_Endpoint[T], Queue[T]] = {}

    def add_receiver(self, endpoint: _Endpoint[T]) -> None:
        """Add a receiver to the channel."""
        super().add_receiver(endpoint)
        self._queues[endpoint] = Queue[T](maxsize=0)

    def remove_receiver(self, endpoint: _Endpoint[T]) -> None:
        """Remove a receiver from the channel."""
        super().remove_receiver(endpoint)
        self._queues.pop(endpoint)

    async def send(self, _endpoint: _Endpoint[T], value: T) -> None:
        """Send a value to the channel."""
        if self._copy_on_send and not isinstance(value, SupportsCopy):
            raise TypeError("Sent value has to implement SupportsCopy protocol to satisfy copy_on_send setting")

        if not self.receivers_available.is_set():
            raise DisconnectedError("Cannot send when there are no open receivers")

        for queue in tuple(self._queues.values()):  # create a snapshot of the queues to avoid race
            if self._copy_on_send:
                value = value.copy()  # type: ignore[reportAssignmentType] # already guarded above
            queue.put_nowait(value)

    async def receive(self, endpoint: _Endpoint[T]) -> T:
        """Receive a value from the channel."""
        if not self.senders_available.is_set():
            raise DisconnectedError("Cannot receive when there are no open senders")

        return await self._queues[endpoint].get()


class _RendezvousChannel(_Channel[T]):
    """Channel that is used to communicate in rendezvous pattern.

    There is no buffering. Sender blocks until receiver is ready to consume the value, and vice versa.
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._senders: deque[tuple[T, Event, Task]] = deque()
        self._receivers: deque[tuple[Event, Task]] = deque()

    async def send(self, _endpoint: _Endpoint[T], value: T) -> None:
        """Send a value to the channel."""
        if self.copy_on_send:
            if not isinstance(value, SupportsCopy):
                raise TypeError("Sent value has to implement SupportsCopy protocol to satisfy copy_on_send setting")
            value = value.copy()

        if not self.receivers_available.is_set():
            raise DisconnectedError("Cannot send when there are no open receivers")

        # get into the queue of senders
        event = Event()
        self._senders.append((value, Event(), current_task()))

        # try to wakeup the first available receiver
        while self._receivers:
            wakeup_event, receiver_task = self._receivers.popleft()
            if not receiver_task.done():
                wakeup_event.set()
                break

        # wait for the rendezvous
        await event.wait()

    async def receive(self, _endpoint: _Endpoint[T]) -> T:
        """Receive a value from the channel."""
        if not self.senders_available.is_set():
            raise DisconnectedError("Cannot receive when there are no open senders")

        while True:
            # try to get the value from the first available sender
            while self._senders:
                value, ack_event, sender_task = self._senders.popleft()
                if not sender_task.done():
                    ack_event.set()
                    return value

            # no senders available, get into the queue of receivers
            event = Event()
            self._receivers.append((event, current_task()))

            # wait for the rendezvous
            await event.wait()


class _Endpoint[T](ABC):
    """Base class for endpoints.

    Designed to be instantiated only by the global `create(...)` function.
    """

    def __new__(cls, *_args: Any, **_kwargs: Any) -> Self:
        raise TypeError(f"Cannot instantiate {cls.__name__} directly, use klever.channel.create(...) function instead.")

    def _init(self, channel: _Channel[T]) -> None:
        """Initialize the endpoint."""
        self._channel: _Channel[T] | None = channel

    @classmethod
    def _create(cls, channel: _Channel[T]) -> Self:
        """Create a new endpoint bound to the given channel."""
        self = object.__new__(cls)
        cls._init(self, channel)
        return self

    def __repr__(self) -> str:
        """Return a string representation of the endpoint."""
        base_repr = f"<{self.__class__.__name__} @{id(self):#x}"
        if self._channel is None:
            return f"{base_repr} closed>"
        return f"{base_repr} bound to {self._channel!r}>"

    async def clone(self) -> Self:
        """Clone the endpoint to create another endpoint bound to the same channel."""
        if self._channel is None:
            raise ValueError("Cannot clone a closed endpoint")
        async with self._channel.lock:
            # lock is required because channel state is modified
            return self.__class__._create(self._channel)  # noqa: SLF001 # call of private method is intentional

    @property
    def is_closed(self) -> bool:
        """Whether the endpoint is closed."""
        return self._channel is None

    def same_channel(self, other: Self) -> bool:
        """Check if the endpoint is bound to the same channel."""
        if self._channel is None or other._channel is None:  # noqa: SLF001 # other is the same type as self
            return False
        return self._channel is other._channel  # noqa: SLF001 # other is the same type as self

    async def __aenter__(self) -> Self:
        """Enter the context manager."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the context manager."""
        await self.close()

    @abstractmethod
    async def close(self) -> None:
        """Close the endpoint."""
        raise NotImplementedError("close is not implemented")


@final
class Sender(_Endpoint[SenderType_contra]):
    """Endpoint for producer that allows to send items to the channel."""

    def _init(self, channel: _Channel[SenderType_contra]) -> None:
        super()._init(channel)
        if channel.only_single_producer and channel.senders_available.is_set():
            raise ValueError(
                f"Cannot create new {self.__class__.__name__} endpoint,"
                " only single producer is allowed for this channel."
            )
        channel.add_sender(self)

    async def send(self, value: SenderType_contra) -> None:
        """Send a value to the channel."""
        if self._channel is None:
            raise ClosedError(f"Cannot send on closed endpoint {self!r}")

        await self._channel.send(self, value)

    async def send_eventually(self, value: SenderType_contra) -> None:
        """Send a value to the channel, waiting for receivers if needed.

        This method will keep retrying to send until successful.
        If there are no receivers, it waits for them to connect and retries.

        Raises:
            ClosedError: if this endpoint is closed.

        """
        while True:
            try:
                await self.send(value)
            except DisconnectedError:
                await self.wait_for_receivers()

    async def wait_for_receivers(self) -> None:
        """Wait until at least one receiver is connected to the channel.

        This method blocks until there is at least one open receiver endpoint.
        Use this to avoid DisconnectedError when sending.

        Raises:
            ClosedError: if this endpoint is closed.

        """
        if self._channel is None:
            raise ClosedError(f"Cannot wait on closed endpoint {self!r}")
        await self._channel.receivers_available.wait()

    async def close(self) -> None:
        """Close the endpoint.

        If the endpoint is already closed, the operation is a no-op.
        """
        if self._channel is None:
            return

        async with self._channel.lock:  # below modifies channel state
            self._channel.remove_sender(self)
        self._channel = None

    async def derive_receiver(self) -> Receiver[SenderType_contra]:
        """Derive a new receiver endpoint bound to the same channel as this sender."""
        if self._channel is None:
            raise ClosedError(f"Cannot derive from closed endpoint {self!r}")

        async with self._channel.lock:  # below modifies channel state
            return Receiver._create(self._channel)  # noqa: SLF001 # call of private method is intentional


@final
class Receiver(_Endpoint[ReceiverType_co]):
    """Endpoint for receiver that allows to receive items from the channel."""

    def _init(self, channel: _Channel[ReceiverType_co]) -> None:
        super()._init(channel)
        if channel.only_single_consumer and channel.receivers_available.is_set():
            raise ValueError(
                f"Cannot create new {self.__class__.__name__} endpoint, "
                "only single consumer is allowed for this channel"
            )
        channel.add_receiver(self)

    def __aiter__(self) -> Self:
        """Return the receiver as an iterator."""
        return self

    async def __anext__(self) -> ReceiverType_co:
        """Receive a value from the channel."""
        try:
            return await self.receive()
        except DisconnectedError as e:
            raise StopAsyncIteration from e

    async def receive(self) -> ReceiverType_co:
        """Receive a value from the channel, blocking if necessary."""
        if self._channel is None:
            raise ClosedError(f"Cannot receive on closed endpoint {self!r}")

        return await self._channel.receive(self)

    async def receive_eventually(self) -> ReceiverType_co:
        """Receive a value from the channel, waiting for senders if needed.

        This method will keep retrying to receive until successful.
        If there are no senders, it waits for them to connect and retries.

        Raises:
            ClosedError: if this endpoint is closed.

        """
        while True:
            try:
                return await self.receive()
            except DisconnectedError:
                await self.wait_for_senders()

    async def wait_for_senders(self) -> None:
        """Wait until at least one sender is connected to the channel.

        This method blocks until there is at least one open sender endpoint.
        Use this to avoid DisconnectedError when receiving.

        Raises:
            ClosedError: if this endpoint is closed.

        """
        if self._channel is None:
            raise ClosedError(f"Cannot wait on closed endpoint {self!r}")
        await self._channel.senders_available.wait()

    async def close(self) -> None:
        """Close the endpoint."""
        if self._channel is None:
            return

        async with self._channel.lock:  # below modifies channel state
            self._channel.remove_receiver(self)
        self._channel = None

    async def derive_sender(self) -> Sender[ReceiverType_co]:
        """Derive a new sender endpoint bound to the same channel as this receiver."""
        if self._channel is None:
            raise ClosedError(f"Cannot derive from closed endpoint {self!r}")

        async with self._channel.lock:  # below modifies channel state
            return Sender._create(self._channel)  # noqa: SLF001 # call of private method is intentional


def create[T](
    capacity: int = 0,
    broadcast: bool = False,
    copy_on_send: bool = False,
    only_single_producer: bool = False,
    only_single_consumer: bool = False,
) -> tuple[Sender[T], Receiver[T]]:
    """Create a new channel and provide a pair of endpoints for communication.

    Endpoints are clonable, so SPSC, MPSC, MPMC, etc. patterns are supported.

    Arguments:
        capacity: capacity of the channel buffer. If 0 (default), a rendezvous channel is created
            where sender blocks until receiver is ready. Ignored in broadcast mode.
        broadcast: if True, the channel will be created in broadcast mode where each receiver
            gets every sent item. Broadcast mode always uses unlimited capacity.
        copy_on_send: if True, the value will be copied on send. Required for mutable objects
            in broadcast mode or when the same value shouldn't be shared between sender and receiver.
        only_single_producer: if True, cloning or deriving new Sender endpoints is prohibited
        only_single_consumer: if True, cloning or deriving new Receiver endpoints is prohibited

    Returns:
        A tuple of (Sender, Receiver) endpoints bound to the created channel.

    """
    common_kwargs = {
        "copy_on_send": copy_on_send,
        "only_single_producer": only_single_producer,
        "only_single_consumer": only_single_consumer,
    }

    if broadcast:
        channel = _BroadcastChannel[T](**common_kwargs)
    elif capacity == 0:
        channel = _RendezvousChannel[T](**common_kwargs)
    else:
        channel = _QueueChannel[T](**common_kwargs, capacity=capacity)

    return (Sender[T]._create(channel), Receiver[T]._create(channel))  # noqa: SLF001
