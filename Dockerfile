FROM python:3-alpine
RUN apk upgrade --no-cache
WORKDIR /app
COPY . .
ENV PORT=80
EXPOSE 80
# Static files served on all interfaces; honors the platform's $PORT.
CMD python3 -m http.server "$PORT" --bind 0.0.0.0
