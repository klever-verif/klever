from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class Named(Protocol):
    @property
    def name(self) -> str: ...


@runtime_checkable
class Printable(Protocol):
    def __str__(self) -> str: ...
    def __repr__(self) -> str: ...


@runtime_checkable
class Hierarchical(Named, Protocol):
    @property
    def parent(self) -> Hierarchical | None: ...
    @property
    def path(self) -> str: ...


@runtime_checkable
class Transaction(Named, Printable, Protocol):
    pass


@runtime_checkable
class SupportsGet(Protocol):
    async def get(self) -> Transaction: ...
    def get_nowait(self) -> Transaction: ...


@runtime_checkable
class SupportsPut(Protocol):
    async def put(self, item: Transaction) -> None: ...
    def put_nowait(self, item: Transaction) -> None: ...


@runtime_checkable
class QueueState(Protocol):
    def qsize(self) -> int: ...
    def empty(self) -> bool: ...
    def full(self) -> bool: ...
    @property
    def maxsize(self) -> int: ...


@runtime_checkable
class QueueLike(SupportsGet, SupportsPut, QueueState, Protocol): ...


@runtime_checkable
class Input(Hierarchical, SupportsGet, Protocol):
    def receive_from(self, source: SupportsGet | Output) -> None: ...
    def as_sink(self) -> SupportsPut: ...


@runtime_checkable
class Output(Hierarchical, SupportsPut, Protocol):
    def send_to(self, sink: SupportsPut | Input) -> None: ...
    def as_source(self) -> SupportsGet: ...


@runtime_checkable
class Transactor(Hierarchical, Protocol):
    async def run(self) -> None: ...
