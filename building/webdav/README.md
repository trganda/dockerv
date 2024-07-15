# Simple Webdav Server

This docker image was build with [httpd:2.4.58](https://hub.docker.com/layers/library/httpd/2.4.58/images/sha256-42ed559bb8529283236b537155e345b47051ed082200c7d7e155405b3e169235?context=explore), it support all platform that it supports.

## Usage

The https was enabled by default, you can overwrite the generated certificate file with volumes

```yaml
version: "3"

services:
  webdav:
    image: jongsx/webdav:2.0.0
    container_name: webdav
    environment:
      - USERNAME=trganda
      - PASSWORD=changeme
    volumes:
      - ./dav:/var/lib/webdav
      - ./conf/cert.crt:/usr/local/apache2/conf/server.crt
      - ./conf/privkey.key:/usr/local/apache2/conf/server.key
    ports:
      - 443:443

volumes:
  webdav-data:
```

For command line setup

```bash
docker run --restart always -v ./dav:/var/lib/webdav \
    -e USERNAME=trganda -e PASSWORD=changeme \
    --publish 443:443 -d jongsx/webdav
```
