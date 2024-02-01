from typing import Generic, TypeVar

import numpy as np
from numpy.typing import NDArray

NumpyDataType = TypeVar("NumpyDataType", bound=np.generic)


class RingBuffer(Generic[NumpyDataType]):
    def __init__(self, capacity: int, dtype: type[NumpyDataType]) -> None:
        self._capacity = capacity
        self._array = np.zeros(shape=capacity, dtype=dtype)
        self._next_index = 0
        self._size = 0

    @property
    def capacity(self) -> int:
        """The maximum number of elements the buffer can hold"""
        return self._capacity

    @property
    def size(self) -> int:
        """The number of elements currently stored in the buffer"""
        return self._size

    @property
    def array(self) -> NDArray[NumpyDataType]:
        """A read-only view of the underlying array containing the user-inserted elements
        Note: The returned array may be smaller than its capacity if the buffer had less elements inserted yet"""
        return self._array[: self._size].view()

    def append(self, value: float | int) -> None:
        self._array[self._next_index] = value
        self._next_index = (self._next_index + 1) % self._capacity
        self._size = min(self._size + 1, self._capacity)

    def append_all(self, values: NDArray[NumpyDataType]) -> None:
        num_values = len(values)
        assert num_values <= self._capacity

        first_part_len = min(num_values, self._capacity - self._next_index)

        # Fill as much as possible without wrapping around
        self._array[self._next_index : self._next_index + first_part_len] = values[:first_part_len]

        # Fill from the beginning if there are remaining elements
        if num_values > first_part_len:
            second_part_len = num_values - first_part_len
            self._array[:second_part_len] = values[first_part_len:]

        self._next_index = (self._next_index + num_values) % self._capacity
        self._size = min(self._size + num_values, self._capacity)

    def recent(self, n: int) -> NDArray[NumpyDataType]:
        """Get the last n inserted elements of the buffer as read-only view.
        Note: The returned array may be smaller than n if the buffer had less than n elements inserted yet"""
        assert 0 <= n <= self._capacity

        if self._size == 0:
            return np.array([], dtype=self._array.dtype)

        n = min(n, self._size)

        end_index = self._next_index
        start_index = (self._next_index - n) % self._capacity

        if start_index < end_index:
            return self._array[start_index:end_index].view()
        else:
            return np.concatenate([self._array[start_index:], self._array[:end_index]]).view()
