FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends bash cowsay fortune-mod fortunes-min netcat-openbsd ca-certificates && rm -rf /var/lib/apt/lists/*
ENV PATH="/usr/games:${PATH}"
RUN useradd --uid 10001 --create-home app
WORKDIR /home/app
COPY --chown=10001:10001 wisecow.sh ./wisecow.sh
USER 10001:10001
EXPOSE 4499
ENTRYPOINT ["bash", "./wisecow.sh"]
