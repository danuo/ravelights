FROM python:3.12

WORKDIR /app

# Install PortAudio dependency for PyAudio
RUN apt-get update && apt-get install -y portaudio19-dev 

# Fix inclusion of numpy headers for installation of aubio package
# See https://github.com/aubio/aubio/issues/320
RUN pip install numpy==1.26.3
RUN export CFLAGS=-I$(python -c "import numpy; print(numpy.get_include())")

# Install dependencies only.
# The complete ravelights app must be mounted to /app when running the container
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md
COPY src/ravelights/constants.py /app/src/ravelights/constants.py

RUN pip install -e .[audio]
