import numpy as np
from ravelights.audio.ring_buffer import RingBuffer


def test_ring_buffer():
    buffer = RingBuffer(capacity=5, dtype=np.float32)

    assert buffer.array.tolist() == [0, 0, 0, 0, 0]

    buffer.append(1)
    buffer.append(2)
    buffer.append(3)

    assert buffer.array.tolist() == [1, 2, 3, 0, 0]

    buffer.append_all(np.array([10, 20, 30], dtype=np.float32))
    assert buffer.array.tolist() == [30, 2, 3, 10, 20]

    buffer.append_all(np.array([100, 200, 300], dtype=np.float32))
    assert buffer.array.tolist() == [30, 100, 200, 300, 20]
    assert buffer.recent(3).tolist() == [100, 200, 300]

    buffer.append_all(np.array([1000, 2000, 3000], dtype=np.float32))
    assert buffer.array.tolist() == [2000, 3000, 200, 300, 1000]
    assert buffer.recent(3).tolist() == [1000, 2000, 3000]
