FROM debian:bookworm-slim

COPY pidocker-ssh-setup /usr/local/bin/pidocker-ssh-setup
COPY pidocker-git /usr/local/bin/git

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git gnupg nodejs npm openssh-client python3 python3-pytest \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL -o /tmp/microsoft.asc https://packages.microsoft.com/keys/microsoft.asc \
    && gpg --dearmor -o /etc/apt/keyrings/microsoft.gpg /tmp/microsoft.asc \
    && chmod go+r /etc/apt/keyrings/microsoft.gpg \
    && rm /tmp/microsoft.asc \
    && printf '%s\n' \
      'Types: deb' \
      'URIs: https://packages.microsoft.com/repos/azure-cli/' \
      'Suites: bookworm' \
      'Components: main' \
      "Architectures: $(dpkg --print-architecture)" \
      'Signed-by: /etc/apt/keyrings/microsoft.gpg' \
      > /etc/apt/sources.list.d/azure-cli.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends azure-cli \
    && npm install -g n \
    && n lts \
    && npm install -g @mariozechner/pi-coding-agent \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && chmod 755 /usr/local/bin/pidocker-ssh-setup /usr/local/bin/git \
    && useradd --create-home --home-dir /home/pi --shell /bin/bash pi \
    && mkdir -p /home/pi/.npm-global /home/pi/.pidocker/secrets /home/pi/.pi/agent /workspace/repos \
    && NPM_CONFIG_PREFIX=/home/pi/.npm-global npm install -g pi-web-access \
    && printf '%s\n' '{"packages":["npm:pi-web-access"]}' > /home/pi/.pi/agent/settings.json \
    && printf '%s\n' \
      'export NPM_CONFIG_PREFIX=/home/pi/.npm-global' \
      'case ":${PATH}:" in *:/home/pi/.npm-global/bin:*) ;; *) export PATH="/home/pi/.npm-global/bin:${PATH}" ;; esac' \
      > /etc/profile.d/pidocker-npm-global.sh \
    && chmod 644 /etc/profile.d/pidocker-npm-global.sh \
    && chmod 700 /home/pi/.pidocker /home/pi/.pidocker/secrets \
    && chown -R pi:pi /home/pi /workspace

ENV NPM_CONFIG_PREFIX=/home/pi/.npm-global
ENV PATH=/home/pi/.npm-global/bin:/usr/local/bin:/usr/local/sbin:/usr/sbin:/usr/bin:/sbin:/bin

USER pi
WORKDIR /workspace/repos

CMD ["pi"]
