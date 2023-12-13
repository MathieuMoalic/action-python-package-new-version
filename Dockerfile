FROM ubuntu:latest
RUN apt-get update && \
    apt-get install -y curl jq && \
    rm -rf /var/lib/apt/lists/*
ADD entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]