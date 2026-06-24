FROM golang:1.25-bookworm AS actionlint

RUN go install github.com/rhysd/actionlint/cmd/actionlint@latest

FROM python:3.12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
      bash \
      ca-certificates \
      curl \
      git \
      make \
      openssh-client \
      shellcheck \
      sshpass \
    && rm -rf /var/lib/apt/lists/*

COPY --from=actionlint /go/bin/actionlint /usr/local/bin/actionlint

WORKDIR /workspace

COPY requirements-dev.txt /tmp/requirements-dev.txt
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r /tmp/requirements-dev.txt
