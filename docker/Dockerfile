FROM debian:bookworm-slim

RUN useradd --create-home --home-dir /home/pi --shell /bin/bash pi \
    && mkdir -p /workspace/repos \
    && chown -R pi:pi /home/pi /workspace

USER pi
WORKDIR /workspace

CMD ["bash"]
