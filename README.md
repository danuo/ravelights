# ravelights

A light installation for raves, consisting of multiple tubes with individually addressable LED strips.

The high-level software in this repository is responsible for generating frames and sending them to the [low-level pixel driver](https://github.com/niliha/ravelights-pixeldriver) via [Art-Net](https://en.wikipedia.org/wiki/Art-Net).

# Getting started

Make sure to pull this repository with the `--recurse-submodules` flag if you plan to serve the web interface using
flask, e.g. 

```
git clone --recurse-submodules git@github.com:niliha/ravelights.git
```

Furthermore, Python 3.10 must be installed.

On linux, it might be required to run

```
sudo sysctl net.ipv4.ip_unprivileged_port_start=80
```

to make port 80 work as unprivileged user.




## Setup virtual environment

This is optional. To create a virtual environment, run

```
python3 -m venv .env
```

To activate, run:

```
.env\Scripts\activate.bat  // windows
source .env/bin/activate   // Unix
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


## Update web interface

Run 

```
git submodule update --remote
```

to fetch the latest static files for the web interface.
