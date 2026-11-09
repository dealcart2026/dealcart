FROM python:3-alpine

# Refresh OS packages at build time and force the fixed zlib release
# (ALPINE-CVE-2026-4738: zlib 1.3.2-r1 -> 1.4-r0) into the final image.
RUN apk upgrade --no-cache \
 && apk add --no-cache --upgrade zlib \
 && rm -rf /var/cache/apk/*

WORKDIR /app
COPY . .

ENV PORT=80
EXPOSE 80

# Static files served on all interfaces; honors the platform's $PORT.
CMD ["sh", "-c", "exec python3 -m http.server ${PORT} --bind 0.0.0.0"]
