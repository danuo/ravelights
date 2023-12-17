# RaveLights

<div align="center">
<video src="https://github.com/danuo/ravelights/assets/66017297/5034c1e2-3bce-451d-8af5-c48d52046552" width="600" autoplay muted loop />
</div>

Ravelights is a library for LED stripes or similar light fixtures. It aims to offer more interesting and advanced visual patterns than similar libraries such as [LedFx](https://github.com/LedFx/LedFx) and [ColorChord](https://github.com/cnlohr/colorchord). This is achieved by providing a rendering pipeline that is used to chain together visual generators. Through variation of the generators used and other settings, endless different visual performances can be achieved. The visual output can by synchronized with the music by using bpm (beats per minute) system.

Ravelights is written in Python and leverages Numpy for fast rendering. It runs reasonably fast and can be run on a Raspberry Pi 3B+ to control ~5000 Leds at 20 fps.

Ravelights also features a user interface written in Quasar (vue.js / rest api) for realtime interaction. Rivelights also provides various interfaces to connect different light fixtures. Currently, Serial/Artnet and UDP/Artnet transmitters are implemented, but additional transmitters can easily be added. The generated output can be routed and distributed through one ore more transmitters at the same time. For example, frames can be sent to [low-level pixel driver](https://github.com/niliha/ravelights-pixeldriver) via [Art-Net](https://en.wikipedia.org/wiki/Art-Net).

# Features

- 30+ Patterns, Vfilters and Dimmers and Effects that can be combined to create unique visual output.
- Web-UI offers fine grained control and programming in realtime.
- BPM system to match the music tempo
- Visualizer to preview the image output, without having access to the actual image fixtures

# Examples

To generate image output, many patterns and effects are implemented already. More so called generators can easily be added (see usage).

<div align="center">
<video src="https://github.com/danuo/ravelights/assets/66017297/939be6d3-719e-4f0e-82e8-510bf6928826" width="600" autoplay muted loop />
</div>

# Installation

### Requirements

- Python 3.10 environment (Windows/Linux/MacOS)
- Linux, make port 80 work as unprivileged user:

```
sudo sysctl net.ipv4.ip_unprivileged_port_start=80
```

### Git

Clone with `--recurse-submodules` flag for web interface submodule:

```
git clone --recurse-submodules git@github.com:danuo/ravelights.git
git submodule update --init    // add submodule after normal cloning
git submodule update --remote  // update submodules
```

### Setup virtual environment

This is optional. To create a virtual environment, run

```
python3 -m venv .env

.env\Scripts\activate.bat  // activate on windows
source .env/bin/activate   // activate on Unix
```

### Install python package

To install, run

```
pip install .[gui]         // normal installation with visualizer support
pip install .              // normal installation without visualizer support
pip install .[serial]      // normal installation without visualizer support but artnet-over-serial support
pip install -e .[gui,dev]  // editable installation with dev packages and visualizer support
```

### Usage

Run `main.py --help`

### Add generators

Patterns, VFilters, Dimmers and Thinners are so called Generators. They are used in combination to generate the visual output. To create a new pattern, the following steps have to be performed.

1. Create a new class that inherits from `Pattern`
2. Implement the required functions, most importantly render() for the visual output.
3. Register the new pattern for usage in `configs/components.py`
