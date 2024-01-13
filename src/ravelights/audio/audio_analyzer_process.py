import random
import time
from multiprocessing.connection import PipeConnection


def audio_analyzer_process(connection: PipeConnection):
    while True:
        # send random data at high rate
        random_data = {
            "random_float": random.random(),
            "random_bool": random.random() > 0.5,
        }
        print(f"sending {random_data}")
        connection.send(random_data)
        time.sleep(1 / 100)
