FROM quic_mvfst:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y pkg-config autoconf curl zip unzip tar build-essential autoconf nasm libtool && \
    rm -rf /var/lib/apt/lists/*

RUN git config --global --add safe.directory /mvfst

WORKDIR /vcpkg

RUN groupadd -g 1001 proxygen && \
    useradd -u 1000 -g 1001 -m proxygen

COPY initial_setup.sh /
RUN chmod +x /initial_setup.sh

USER proxygen

CMD ["bash"]
