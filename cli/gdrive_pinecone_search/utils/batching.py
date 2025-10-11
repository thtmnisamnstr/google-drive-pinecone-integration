"""Utility helpers for batching iterables."""

from typing import Iterable, Iterator, List, TypeVar

T = TypeVar("T")


def batch_iterable(iterable: Iterable[T], batch_size: int) -> Iterator[List[T]]:
    """Yield lists of up to ``batch_size`` items from ``iterable``.

    Args:
        iterable: Any iterable source.
        batch_size: Maximum number of items per batch (must be > 0).

    Yields:
        Lists containing up to ``batch_size`` elements preserving input order.
    """

    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")

    batch: List[T] = []
    for item in iterable:
        batch.append(item)
        if len(batch) == batch_size:
            yield batch
            batch = []

    if batch:
        yield batch

