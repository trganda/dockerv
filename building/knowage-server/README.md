# Docker Image for Knowage

[![Docker badge](https://img.shields.io/docker/pulls/knowagelabs/knowage-server-docker.svg)](https://hub.docker.com/r/knowagelabs/knowage-server-docker/)

## What is Knowage?

Knowage is the professional open source suite for modern business analytics over traditional sources and big data systems.

> [knowage-suite.com](https://www.knowage-suite.com)

## Run Knowage

Differently from its predecessor (i.e. SpagoBI), you can use ```docker-compose``` or ```Docker Swarm``` for running Knowage with a [MariaDB container](https://hub.docker.com/_/mariadb). This will be shipped with within a single command.

Both ways need to be defined by a simple text file in [YAML](https://docs.docker.com/compose/compose-file/) format that describes which containers must be run.

Pay attention that for both YAML files in this project, the DBMS stores its data in a volume called ```db``` to make them permanent between multiple run of the DBMS. If you want to reset DB data you need to delete that volume.

### Use docker-compose

If you want to run Knowage on your local machine, with minimum configuration, for testing purpose, run this command inside the folder with ```docker-compose.yml``` file:

```console
$ docker-compose up
```

This launch the DBMS and Knowage in attached mode: here you can see logs of both the container at the same time. To stop both containers you can use ```CTRL+C```. If you want to run Knowage in detached mode use ```-d``` option like:

```console
$ docker-compose up -d
```

If you want to remove all the containers that Knowage created, just use:

```console
$ docker-compose down
```

By default, the available users are:

|User   |Password|
|-------|--------|
|biadmin|biadmin |
|bidev  |bidev   |
|biuser |biuser  |
