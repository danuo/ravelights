from typing import Generic, TypeVar

import numpy as np
from numpy.typing import NDArray

NumpyDataType = TypeVar("NumpyDataType", bound=np.generic)


class RingBuffer(Generic[NumpyDataType]):
    def __init__(self, capacity: int, dtype: type[NumpyDataType]) -> None:
        self._capacity = capacity
        self._array = np.zeros(shape=capacity, dtype=dtype)
        self._next_index = 0

    @property
    def array(self) -> NDArray[NumpyDataType]:
        """A read-only view of the underlying array"""
        return self._array.view()

    def append(self, value: float | int) -> None:
        self._array[self._next_index] = value
        self._next_index = (self._next_index + 1) % self._capacity

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

    def recent(self, n: int) -> NDArray[NumpyDataType]:
        """Get the last n inserted elements of the buffer"""
        assert 0 <= n <= self._capacity

        end_index = self._next_index
        start_index = (self._next_index - n) % self._capacity

        if start_index < end_index:
            return self._array[start_index:end_index]
        else:
            return np.concatenate([self._array[start_index:], self._array[:end_index]])
