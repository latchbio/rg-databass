from typing import TypeVar


T = TypeVar("T")


def shift_right(xs: list[T], /, base: int) -> None:
    """
    >>> xs = [1, 2, 3, 4, -999]; shift_right(xs, base=0); xs
    [1, 1, 2, 3, 4]
    >>> xs = [1, 2, 3, 4, -999]; shift_right(xs, base=1); xs
    [1, 2, 2, 3, 4]
    >>> xs = [1, 2, 3, 4, -999]; shift_right(xs, base=2); xs
    [1, 2, 3, 3, 4]
    >>> xs = [1, 2, 3, 4, -999]; shift_right(xs, base=3); xs
    [1, 2, 3, 4, 4]
    >>> xs = [1, 2, 3, 4, -999]; shift_right(xs, base=4); xs
    [1, 2, 3, 4, -999]
    >>> xs = [1, 2, 3, 4, -999]; shift_right(xs, base=5); xs
    Traceback (most recent call last):
        ...
    IndexError: shift base out of range
    >>> xs = [1, 2, 3, 4, -999]; shift_right(xs, base=-1); xs
    [1, 2, 3, 4, -999]
    >>> xs = [1, 2, 3, 4, -999]; shift_right(xs, base=-2); xs
    [1, 2, 3, 4, 4]
    """
    while base < 0:
        base += len(xs)

    if base > len(xs) - 1:
        raise IndexError("shift base out of range")

    xs[base + 1 :] = xs[base:-1]


def shift_left(xs: list[T], /, base: int) -> None:
    """
    >>> xs = [1, 2, 3, 4, 5]; shift_left(xs, base=0); xs
    [2, 3, 4, 5, 5]
    >>> xs = [1, 2, 3, 4, 5]; shift_left(xs, base=1); xs
    [1, 3, 4, 5, 5]
    >>> xs = [1, 2, 3, 4, 5]; shift_left(xs, base=2); xs
    [1, 2, 4, 5, 5]
    >>> xs = [1, 2, 3, 4, 5]; shift_left(xs, base=3); xs
    [1, 2, 3, 5, 5]
    >>> xs = [1, 2, 3, 4, 5]; shift_left(xs, base=4); xs
    [1, 2, 3, 4, 5]
    >>> xs = [1, 2, 3, 4, 5]; shift_left(xs, base=5); xs
    Traceback (most recent call last):
        ...
    IndexError: shift base out of range
    >>> xs = [1, 2, 3, 4, 5]; shift_left(xs, base=-1); xs
    [1, 2, 3, 4, 5]
    >>> xs = [1, 2, 3, 4, 5]; shift_left(xs, base=-2); xs
    [1, 2, 3, 5, 5]
    """
    while base < 0:
        base += len(xs)

    if base > len(xs) - 1:
        raise IndexError("shift base out of range")

    xs[base:-1] = xs[base + 1 :]
