from dataclasses import dataclass
from typing import Callable, Iterator, Sequence, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Window:
    start: float
    end: float
    records: Sequence


def step_seconds(width_sec: float, overlap: float) -> float:
    return width_sec * (1 - overlap)


def sliding_windows(
    records: Sequence[T],
    timestamp_fn: Callable[[T], float],
    width_sec: float,
    overlap: float,
) -> Iterator[Window]:
    if not records:
        return

    step = step_seconds(width_sec, overlap)
    if step <= 0:
        raise ValueError(
            f"overlap {overlap!r} yields a non-positive step for width {width_sec!r}"
        )

    ordered = sorted(records, key=timestamp_fn)
    t0 = timestamp_fn(ordered[0])
    t_last = timestamp_fn(ordered[-1])

    start = t0
    while start <= t_last:
        end = start + width_sec
        window_records = [r for r in ordered if start <= timestamp_fn(r) < end]
        yield Window(start=start, end=end, records=window_records)
        start += step
