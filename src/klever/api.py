from __future__ import annotations

import asyncio
from collections.abc import Iterable
from typing import TYPE_CHECKING

from .types import (
    Hierarchical,
    Input,
    Named,
    Output,
    QueueLike,
    QueueState,
    SupportsGet,
    SupportsPut,
    Transaction,
    Transactor,
)


class HierarchicalMixin:
    """Mixin for objects that have a name and parent and a path in the hierarchy.

    This mixin implements the `Hierarchical` protocol.
    """

    __slots__ = ("__name", "__parent")

    def __init__(self, *, name: str, parent: Hierarchical | None = None, **kwargs):
        self.__name = name
        self.__parent = parent
        super().__init__(**kwargs)

    @property
    def parent(self) -> Hierarchical | None:
        return self.__parent

    @property
    def name(self) -> str:
        return self.__name

    @property
    def path(self) -> str:
        if self.parent is None:
            return self.name
        return f"{self.parent.path}.{self.name}"


if TYPE_CHECKING:
    _h0: Named = object.__new__(HierarchicalMixin)
    _h1: Hierarchical = object.__new__(HierarchicalMixin)


class InputsMixin:
    """Mixin for objects that can declare and use inputs."""

    __slots__ = "__ports"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__ports: dict[str, Input] = {}
        if not isinstance(self, Transactor):
            raise TypeError("InputsMixin can only be used on objects that implement the Transactor protocol")

    def declare_input(self, name: str) -> Input:
        if name not in self.__ports:
            assert isinstance(self, Hierarchical)
            self.__ports[name] = Channel(name, parent=self)
        return self.__ports[name]

    def inputs(self) -> Iterable[tuple[str, Input]]:
        return self.__ports.items()

    def input(self, name: str) -> Input:
        return self.__ports[name]


class AsInputMixin:
    """Mixin for objects that can be used as inputs.

    This mixin partly implements the `Input` protocol and
    requires the `Hierarchical` protocol to be implemented on objects that use it.
    """

    __slots__ = "__port"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not isinstance(self, Transactor):
            raise TypeError("AsInputMixin can only be used on objects that implement the Transactor protocol")
        self.__port: Channel = Channel("default", parent=self)

    def receive_from(self, source: SupportsGet | Output) -> None:
        if isinstance(source, Output):
            source = source.as_source()
        self.__port.receive_from(source)

    async def get(self) -> Transaction:
        return await self.__port.get()

    def get_nowait(self) -> Transaction:
        return self.__port.get_nowait()

    def as_sink(self) -> SupportsPut:
        return self.__port


if TYPE_CHECKING:
    _ai0: SupportsGet = object.__new__(AsInputMixin)

    class _AsInputMixin(AsInputMixin, HierarchicalMixin):
        pass

    _ai1: Input = object.__new__(_AsInputMixin)


class OutputsMixin:
    """Mixin for objects that can declare and use outputs."""

    __slots__ = "__ports"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.__ports: dict[str, Output] = {}
        if not isinstance(self, Transactor):
            raise TypeError("AsInputMixin can only be used on objects that implement the Transactor protocol")

    def declare_output(self, name: str) -> Output:
        if name not in self.__ports:
            assert isinstance(self, Hierarchical)
            self.__ports[name] = Channel(name, parent=self)
        return self.__ports[name]

    def outputs(self) -> Iterable[tuple[str, Output]]:
        return self.__ports.items()

    def output(self, name: str) -> Output:
        return self.__ports[name]


class AsOutputMixin:
    """Mixin for objects that can be used as outputs.

    This mixin partly implements the `Output` protocol and
    requires the `Hierarchical` protocol to be implemented on objects that use it.
    """

    __slots__ = "__port"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not isinstance(self, Transactor):
            raise TypeError("AsOutputMixin can only be used on objects that implement the Hierarchical protocol")
        self.__port = Channel("default", parent=self)

    def send_to(self, sink: SupportsPut | Input) -> None:
        if isinstance(sink, Input):
            sink = sink.as_sink()
        self.__port.send_to(sink)

    async def put(self, item: Transaction) -> None:
        await self.__port.put(item)

    def put_nowait(self, item: Transaction) -> None:
        self.__port.put_nowait(item)

    def as_source(self) -> SupportsGet:
        return self.__port


if TYPE_CHECKING:
    ao0: SupportsPut = object.__new__(AsOutputMixin)

    class _AsOutputMixin(AsOutputMixin, HierarchicalMixin):
        pass

    ao1: Output = object.__new__(_AsOutputMixin)


class Channel(HierarchicalMixin):
    """Channel is a bidirectional communication channel between two objects.

    It is a queue-like object that can be used to send and receive transactions between two objects.
    """

    def __init__(self, name: str, parent: Hierarchical | None = None, maxsize: int = 0) -> None:
        super().__init__(name=name, parent=parent)
        self._queue: QueueLike = asyncio.Queue(maxsize)
        self._receive_tasks: dict[SupportsGet, asyncio.Task[None]] = {}
        self._sinks: set[SupportsPut] = set()
        self._dispatch_task: asyncio.Task[None] | None = None

    async def put(self, item: Transaction) -> None:
        await self._queue.put(item)

    def put_nowait(self, item: Transaction) -> None:
        self._queue.put_nowait(item)

    async def get(self) -> Transaction:
        return await self._queue.get()

    def get_nowait(self) -> Transaction:
        return self._queue.get_nowait()

    def qsize(self) -> int:
        return self._queue.qsize()

    def empty(self) -> bool:
        return self._queue.empty()

    def full(self) -> bool:
        return self._queue.full()

    @property
    def maxsize(self) -> int:
        return self._queue.maxsize

    def as_sink(self) -> SupportsPut:
        return self

    def as_source(self) -> SupportsGet:
        return self

    def receive_from(self, source: SupportsGet | Output) -> None:
        if isinstance(source, Output):
            source = source.as_source()

        if source is self:
            raise ValueError("Cannot connect input channel to itself")

        if source in self._receive_tasks:
            return  # idempotent

        name = f"{source.path}->{self.path}" if isinstance(source, Hierarchical) else f"{source!r}->{self.path}"
        task = asyncio.create_task(self._receive_loop(source), name=name)
        self._receive_tasks[source] = task

    async def _receive_loop(self, source: SupportsGet) -> None:
        while True:
            item = await source.get()
            await self.put(item)

    def send_to(self, sink: SupportsPut | Input) -> None:
        if isinstance(sink, Input):
            sink = sink.as_sink()

        if sink is self:
            raise ValueError("Cannot connect input channel to itself")

        if sink in self._sinks:
            return

        self._sinks.add(sink)
        if self._dispatch_task is None or self._dispatch_task.done():
            self._dispatch_task = asyncio.create_task(self._dispatch_loop(), name=f"{self.path}.dispatcher")

    async def _dispatch_loop(self) -> None:
        while True:
            item = await self.get()
            for sink in self._sinks:
                await sink.put(item)


if TYPE_CHECKING:
    _ch0: SupportsGet = object.__new__(Channel)
    _ch1: SupportsPut = object.__new__(Channel)
    _ch2: QueueState = object.__new__(Channel)
    _ch3: Named = object.__new__(Channel)
    _ch4: Hierarchical = object.__new__(Channel)
    _ch6: Input = object.__new__(Channel)
    _ch7: Output = object.__new__(Channel)
    _ch8: QueueLike = object.__new__(Channel)
