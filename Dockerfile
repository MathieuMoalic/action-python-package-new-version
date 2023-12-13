FROM ubuntu:latest
WORKDIR /usr/src/app
RUN apt-get update && \
    apt-get install -y curl jq && \
    rm -rf /var/lib/apt/lists/*
COPY . .
RUN chmod +x ./scripts/check_version.sh
ENTRYPOINT ["./scripts/check_version.sh"]
CMD ["."]