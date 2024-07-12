# ztncui - ZeroTier network controller user interface

ztncui is a web user interface for a standalone [ZeroTier](https://zerotier.com) network controller.

Screenshots can be seen at [key-networks.com/ztncui](https://key-networks.com/ztncui).

Follow us on [![alt @key_networks on Twitter](https://i.imgur.com/wWzX9uB.png)](https://twitter.com/key_networks)

## Usage

Generate a self-signed certificate:

```bash
openssl req -x509 -newkey rsa:4096 -keyout cert.key -out cert.crt -days 365 -nodes -subj "/C=CN"
```

Run the server:

```bash
docker compose up -d
```