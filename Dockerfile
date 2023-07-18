FROM python:3.11

WORKDIR /code

# First step: Install dependencies only.
# This allows docker to cache them as long as pyproject.toml remains unchanged
COPY pyproject.toml /code/pyproject.toml
RUN mkdir src
RUN pip install .

# Second step: Install package including dependencies
# Pip will not reinstall them since they were installed in the previous step
COPY . /code
RUN pip install .
