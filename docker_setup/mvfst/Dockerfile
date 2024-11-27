FROM quic_mvfst:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    rm -rf /var/lib/apt/lists/*

RUN git config --global --add safe.directory /mvfst

WORKDIR /mvfst

RUN groupadd -g 1001 mvfst && \
    useradd -u 1000 -g 1001 -m mvfst

COPY initial_setup.sh /
RUN chmod +x /initial_setup.sh

USER mvfst

CMD ["bash"]
