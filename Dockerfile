# syntax=docker/dockerfile:1
FROM python:3.13-alpine

# mount current directory to /app
# install with pip
RUN --mount=type=bind,rw,source=.,target=/src \
    pip install --no-cache-dir /src

CMD echo "Available commands:" && find /usr/local/bin -type f -name 'solarman*' -exec basename {} \;
