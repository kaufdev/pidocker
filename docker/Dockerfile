FROM debian:bookworm-slim

COPY pidocker-ssh-setup /usr/local/bin/pidocker-ssh-setup

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git nodejs npm openssh-client \
    && npm install -g n \
    && n lts \
    && npm install -g @mariozechner/pi-coding-agent \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && chmod 755 /usr/local/bin/pidocker-ssh-setup \
    && useradd --create-home --home-dir /home/pi --shell /bin/bash pi \
    && mkdir -p /workspace/repos \
    && chown -R pi:pi /home/pi /workspace

USER pi
WORKDIR /workspace

CMD ["pi"]
