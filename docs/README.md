# Full setup for Jetson Nano

__This example describes entire setup that allows for launching multi-azure-recorder on Jetson Nano in local and distributed cases__

## Install
__Clone repo__
```
git clone --recurse-submodules https://github.com/MobileRoboticsSkoltech/multi-azure-recorder
```
__Install components__
```
sudo apt-get update
sudo apt-get install ninja-build \
  libssl-dev \
  libxinerama-dev \
  libxcursor-dev \
  libboost-all-dev \
  libsoundio-dev \
  libjpeg-dev \
  libvulkan-dev \
  libudev-dev \
  curl \
  libk4a1.4-dev
```
__Add Microsoft repo__
```
curl -sSL https://packages.microsoft.com/keys/microsoft.asc | sudo tee /etc/apt/trusted.gpg.d/microsoft.asc
sudo apt-add-repository https://packages.microsoft.com/ubuntu/18.04/multiarch/prod
sudo apt-get update
```

__Add Depth Engine support__
```
sudo apt-get install libk4a1.4-dev
sudo ln -s /usr/lib/aarch64-linux-gnu/libk4a1.4/libdepthengine.so.2.0 /lib/aarch64-linux-gnu/libdepthengine.so.2.0
```

__Add temporary images streaming to RAM__
```
sudo mkdir /mnt/mrob_tmpfs
sudo mount -t tmpfs -o size=512m tmpfs /mnt/mrob_tmpfs
echo 'tmpfs  /mnt/mrob_tmpfs tmpfs nodev,nosuid,noexec,nodiratime,size=512M   0 0' | sudo tee -a /etc/fstab
```

__Add possibility to run azure software without sudo__
```
sudo cp ../scripts/99-k4a.rules /etc/udev/rules.d/
```
__Build__
```
mkdir build && cd build
cmake .. -GNinja
ninja
```

__(For distributed case only) Support remote control__
```
sudo apt install python3.8 # python>=3.6 for websockets>=10 during uvicorn[standard] install
sudo apt-get install python3.8-dev
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1
sudo apt install python3-pip
pip3 install fastapi
pip3 install uvicorn[standard]
```

## Launch recorder (locally or through ssh)
__On Jetson Nano (server)__  
Can be setup by cron, etc to launch during every boot
```
sudo sh -c 'echo 1000 > /sys/module/usbcore/parameters/usbfs_memory_mb' # increase USB buf size
export DISPLAY=:0 # if through SSH to avoid errors
./recorder.py --distributed TRUE
```

## Launch recorder (distributed)
__On server (Jetson Nano)__  
Can be setup by cron, etc to launch during every boot
```
sudo sh -c 'echo 1000 > /sys/module/usbcore/parameters/usbfs_memory_mb' # increase USB buf size
export DISPLAY=:0
uvicorn server:app --host 0.0.0.0 # for distributed case only, in another terminal
```

__On Client (project assumed to be already installed)__
```
./recorder.py --distributed TRUE
```

