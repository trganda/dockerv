
Generate a random certificate

```bash
openssl req -x509 -newkey rsa:2048 -days 1000 -nodes \
    -keyout /certs/cert.key -out /certs/cert.crt -subj "/CN=CN"
```