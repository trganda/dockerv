### Dockerfile for x86_64 Platform Archlinux

This is a image build file for develop on x86_64 platform and vulnerability analyze. 

Run

```bash
docker buildx build --platform linux/x86_64 -t archlinux .
```

### Notice

Before use buildx for cross platform image building, make sure enabled the experimental features on the Docker CLI.
The easiest way is modifed the configuration file `~/.docker/config.json` with

```json
{
    ...
     "experimental": “enabled”
}
```

### Reference

1. https://www.docker.com/blog/multi-platform-docker-builds/