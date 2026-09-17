FROM node:24-alpine AS build

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:alpine

COPY nginx.conf /etc/nginx/templates/default.conf.template
COPY --from=build /app/dist /usr/share/nginx/html

RUN printf '%s\n' \
    '#!/bin/sh' \
    'set -eu' \
    ': "${GATEWAY_URL:?GATEWAY_URL is required (https://gateway-host/api/)}"' \
    ': "${GATEWAY_HOST:?GATEWAY_HOST is required}"' \
    'case "$GATEWAY_HOST" in *[!A-Za-z0-9.-]*) echo "GATEWAY_HOST must be a DNS hostname" >&2; exit 1;; esac' \
    '[ "$GATEWAY_URL" = "https://${GATEWAY_HOST}/api/" ] || { echo "GATEWAY_URL must be https://GATEWAY_HOST/api/" >&2; exit 1; }' \
    > /docker-entrypoint.d/15-validate-gateway.sh \
    && chmod +x /docker-entrypoint.d/15-validate-gateway.sh

ENV NGINX_ENVSUBST_FILTER="^GATEWAY_(URL|HOST)$"

EXPOSE 80
