# ravelights

A light installation for raves, consisting of multiple tubes with individually addressable LED strips.

The high-level software in this repository is responsible for generating frames and sending them to the [low-level pixel driver](https://github.com/niliha/ravelights-pixeldriver) via [Art-Net](https://en.wikipedia.org/wiki/Art-Net).

## Requirements

- Python 3.10 environment (Windows/Linux/MacOS)
- Linux, make port 80 work as unprivileged user:

```
sudo sysctl net.ipv4.ip_unprivileged_port_start=80
```

## Git

Clone with `--recurse-submodules` flag for web interface submodule:

```
git clone --recurse-submodules git@github.com:danuo/ravelights.git
git submodule update --init    // add submodule after normal cloning
git submodule update --remote  // update submodules
```

## Setup virtual environment

This is optional. To create a virtual environment, run

```
python3 -m venv .env

.env\Scripts\activate.bat  // activate on windows
source .env/bin/activate   // activate on Unix
```

## Install python package

To install, run

```
pip install .[gui]         // normal installation with visualizer support
pip install .              // normal installation without visualizer support
pip install .[serial]      // normal installation without visualizer support but artnet-over-serial support
pip install -e .[gui,dev]  // editable installation with dev packages and visualizer support
```

## Usage

Run `main.py --help`
