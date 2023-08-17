FROM python:3.11

WORKDIR /app

# Install dependencies only.
# The complete app must be mounted to /app
COPY pyproject.toml /app/pyproject.toml
RUN mkdir src
RUN pip install -e .[serial]
