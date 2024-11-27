FROM quic_mvfst:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y curl git lsb-release python3 git file vim sudo && \
    rm -rf /var/lib/apt/lists/*

ENV PATH="/depot_tools:${PATH}"

RUN git config --global --add safe.directory /depot_tools && \
    git config --global --add safe.directory /chromium/src

WORKDIR /chromium/src

RUN groupadd -g 1001 quic && \
    useradd -u 1000 -g 1001 -m quic

COPY initial_setup.sh /
RUN chmod +x /initial_setup.sh

USER quic

CMD ["bash"]
