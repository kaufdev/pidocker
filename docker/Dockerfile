FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl nodejs npm \
    && npm install -g n \
    && n lts \
    && npm install -g @mariozechner/pi-coding-agent \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --home-dir /home/pi --shell /bin/bash pi \
    && mkdir -p /workspace/repos \
    && chown -R pi:pi /home/pi /workspace

USER pi
WORKDIR /workspace

CMD ["pi"]
