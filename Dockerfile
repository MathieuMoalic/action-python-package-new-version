FROM ubuntu:latest
WORKDIR /usr/src/app
COPY . .
RUN chmod +x ./scripts/check_version.sh
ENTRYPOINT ["./scripts/check_version.sh"]
CMD ["."]