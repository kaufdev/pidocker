FROM python:3.13-slim-bookworm

ARG PI_CODING_AGENT_VERSION=0.80.6
ARG PI_WEB_ACCESS_VERSION=0.13.0
ARG PI_FIXED_EDITOR_VERSION=0.2.3

COPY pidocker-ssh-setup /usr/local/bin/pidocker-ssh-setup
COPY pidocker-resume-repo.ts /usr/local/share/pidocker/pidocker-resume-repo.ts

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl git gnupg nodejs npm openssh-client \
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
    && printf '%s\n' \
      'Types: deb' \
      'URIs: https://packages.microsoft.com/repos/microsoft-debian-bookworm-prod/' \
      'Suites: bookworm' \
      'Components: main' \
      "Architectures: $(dpkg --print-architecture)" \
      'Signed-by: /etc/apt/keyrings/microsoft.gpg' \
      > /etc/apt/sources.list.d/microsoft-prod.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends azure-cli azure-functions-core-tools-4 \
    && npm install -g n \
    && n lts \
    && npm install -g "@earendil-works/pi-coding-agent@${PI_CODING_AGENT_VERSION}" \
    && python -m pip install --no-cache-dir pytest \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && chmod 755 /usr/local/bin/pidocker-ssh-setup \
    && useradd --create-home --home-dir /home/pi --shell /bin/bash pi \
    && mkdir -p /home/pi/.npm-global /home/pi/.pidocker/secrets /home/pi/.pi/agent /workspace/repos \
    && NPM_CONFIG_PREFIX=/home/pi/.npm-global npm install -g "pi-web-access@${PI_WEB_ACCESS_VERSION}" "@tifan/pi-fixed-editor@${PI_FIXED_EDITOR_VERSION}" \
    && printf '%s\n' '{"packages":["npm:pi-web-access","npm:@tifan/pi-fixed-editor"]}' > /home/pi/.pi/agent/settings.json \
    && printf '%s\n' '{"tui.input.newLine":["shift+enter","ctrl+j"]}' > /home/pi/.pi/agent/keybindings.json \
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
