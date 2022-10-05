FROM borda/docker_python-opencv-ffmpeg:cpu-py3.8-cv4.5.5

ARG ARCH=amd64

############ Part 2: SDK and multirecorder setup #############

RUN apt-get update --allow-unauthenticated && apt-get install -y --allow-unauthenticated \
    file \
    dpkg-dev \
    qemu \
    binfmt-support \
    qemu-user-static \
    pkg-config \
    ninja-build \
    doxygen \
    clang \
    python3 \
    gcc \
    g++ \
    git \
    git-lfs \
    nasm \
    cmake \
    curl \
    gpg-agent \
    libboost-all-dev \
    libgl1-mesa-dev:$ARCH \
    libsoundio-dev:$ARCH \
    libjpeg-dev:$ARCH \
    libvulkan-dev:$ARCH \
    libx11-dev:$ARCH \
    libxcursor-dev:$ARCH \
    libxinerama-dev:$ARCH \
    libxrandr-dev:$ARCH \
    libusb-1.0-0-dev:$ARCH \
    libssl-dev:$ARCH \
    libudev-dev:$ARCH \
    mesa-common-dev:$ARCH \
    uuid-dev:$ARCH

RUN wget https://packages.microsoft.com/config/ubuntu/18.04/packages-microsoft-prod.deb && \
    dpkg -i packages-microsoft-prod.deb && rm packages-microsoft-prod.deb && \
    apt-get update && ACCEPT_EULA=Y apt-get install -y libk4a1.4 libk4a1.4-dev k4a-tools

ADD . /multi-azure-recorder

RUN cd /multi-azure-recorder/Azure-Kinect-Sensor-SDK && \
    mkdir build && cd build && \
    cmake .. -GNinja && \
    ninja

WORKDIR /multi-azure-recorder
