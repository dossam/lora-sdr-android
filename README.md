# Mobile Android SDR-based LoRa Receiver

## Description

This repository contains implementation files and instructions to run an SDR-based LoRa receiver on an Android phone. The receiver is run inside a virtual environment installed on Termux, and uses the SDR implementation from [https://github.com/dossam/pylorasdr](https://github.com/dossam/pylorasdr). It supports RTL-SDR and HackRF through [`rtl_tcp_andro`](https://f-droid.org/fr/packages/marto.rtl_tcp_andro/). Only RTL-SDR is tested for the moment.

## Installation
In addition to the source files of this repository, the receiver requires the `Termux` emulator and `rtl_tcp_andro`.

#### Installation of required tools and setup of proot container
- First install `Termux` from [F-Droid](https://f-droid.org/fr/packages/com.termux.api/). You might need to install F-droid first if not already installed.
Do not install `Termux` from PlayStore, since it is outdated.

- Install `rtl_tcp_andro` from [F-Droid](https://f-droid.org/fr/packages/marto.rtl_tcp_andro/).

- Start `Termux` and update the packages source information:
```
pkg update && pkg upgrade
``` 

- Install `proot-distribution` and `git`:
```
pkg install proot-distro git
```

- Install an Ubuntu distribution inside a `proot` container
```
pd install ubuntu
```

- Start the container
```
pd login ubuntu
```

- Create a `lorasdr` user with a home directory and a `bash` shell
```
useradd lorasdr
mkdir /home/lorasdr
chown lorasdr:lorasdr /home/lorasdr
chsh -s /usr/bin/bash lorasdr
```

#### Creation of a virtual environment and receiver setup
- Install `conda` through `miniforge`
```
su lorasdr
cd $HOME
wget "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-$(uname)-$(uname -m).sh"
bash Miniforge3-$(uname)-$(uname -m).sh
```

- Create a virtual environment with a `python` interpreter
```
source .bashrc
conda create -n pylorasdr python
```

- Clone and install the `pylorasdr` library inside the virtual environment
```
conda activate pylorasdr
git clone https://github.com/dossam/pylorasdr
cd pylorasdr
pip install .
```

- Clone this repo
```
cd ..
git clone https://github.com/dossam/lora-sdr-android
cd lora-sdr-android
```
The `shell_scripts` folder contains two scripts: `start_receiver.sh` used to start the receiver from inside the virtual environment, and `tmux_start_rx.sh` used to start the receiver from `Termux`.

- Make `start_receiver.sh` executable
```
chmod +x shell_scripts/start_receiver.sh
```

- Copy the `tmux_start_rx.sh` to Termux home folder.
```
cp shell_scripts/tmux_start_rx.sh /data/data/com.termux/files/home/
```

- Logout the `lorasdr` user
```
exit
```

- Exit the proot container, back to Termux
```
exit
```

- Make `tmux_start_rx.sh` executable
```
chmod +x tmux_start_rx.sh
```

#### Start the receiver
- The receiver can now be started with
```
./tmux_start_rx.sh --port 12345 --freq 868100000 --sample-rate 250000
```
The script launch the `rtl_tcp` server through an Android intent, and start the receiver.

Make sure the SDR is connected. `--freq` should be set to the appropriate channel frequency, and `--sample-rate` to twice the bandwidth. For example, for a LoRa chip configured with a `125 kHz` bandwidth, the `--sample-rate` should be set to `250000`. The LoRa demodulator is run with a 2x oversampling.

The script also support other optional parameters such as 
- `--addr`: IP address . Defaults to `127.0.0.1`.
- `--sf`: spreading factor. Defaults to `7`.
- `--netid`: network ID. Defaults to `18`. 
- `--upchirps`: number of preamble upchirps.  Defaults to `8`.

With the current implementation, the receiver prints the information related to a received frame: uplink/downlink, the coding rate (CR), the estimated SNR, and the payload. The default behavior can be changed by registering a handler function with `lora_rx.register_frame_handler` in [src/lora_receiver.py](src/lora_receiver.py). For instance, it can be used to forward the received frame through a socket connection.