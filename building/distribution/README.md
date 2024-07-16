# Self-Host Registry for Docker

> https://github.com/distribution/distribution

Generate a random certificate

```bash
openssl req -x509 -newkey rsa:4096 -days 1000 -nodes \
    -keyout cert.key -out cert.crt -subj "/CN=CN"
```

Config authentication

```bash
htpasswd -Bbn <user> <passwd> > auth/htpasswd
```

Start registry

```
docker compose up -d
```