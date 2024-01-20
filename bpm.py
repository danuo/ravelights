from collections import deque

import aubio
import numpy as np
import pyaudio

# Rate to sample from the audio stream
sample_rate = 44100

# Number of frames to to use for the fft
fft_window_size = 1024

# Number of frames to feed into the fft for each new frame.
# If this is smaller than fft_window_size, then the fft will
# have some overlap between frames which is desired
hop_size = fft_window_size // 2

tempo_detection = aubio.tempo("default", fft_window_size, hop_size, sample_rate)

onset_size_multiplier = 4
onset_samples_array = np.zeros(shape=onset_size_multiplier * hop_size, dtype=np.float32)
onset_fft = int(onset_size_multiplier * fft_window_size)
onset_hop_size = int(onset_size_multiplier * hop_size)
onset_detection = aubio.onset("specflux", onset_fft, onset_hop_size, sample_rate)

p = pyaudio.PyAudio()
stream = p.open(
    format=pyaudio.paFloat32,
    channels=1,
    rate=sample_rate,
    input=True,
    frames_per_buffer=hop_size,
)

print("*** starting recording")

beat_times: deque[float] = deque(maxlen=16)
while True:
    try:
        audio_buffer: bytes = stream.read(hop_size)
        samples = np.frombuffer(audio_buffer, dtype=np.float32)

        if tempo_detection(samples):
            volume = np.round(100 * np.mean(np.abs(samples)), decimals=1)

            # Get the timestamp in seconds (float) of this beat
            beat_time = tempo_detection.get_last_s()
            print(f"Got beat at {beat_time}. volume: {volume}")
            beat_times.append(beat_time)
            if len(beat_times) >= 4:
                print("BPM: %f" % (60 / (np.median(np.diff(beat_times)))))

        onset_samples_array[:-hop_size] = onset_samples_array[hop_size:]
        onset_samples_array[-hop_size:] = np.array(samples, dtype=np.float32)
        if onset_detection(onset_samples_array):
            onset_time = onset_detection.get_last_s()
            print(f"Onset detected at {onset_time}")

    except KeyboardInterrupt:
        print("*** Ctrl+C pressed, exiting")
        break

print("*** done recording")
stream.stop_stream()
stream.close()
p.terminate()
