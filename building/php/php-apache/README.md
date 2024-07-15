## Usage

I hava use this enviroment to learning unserialization risks in php [session](https://github.com/80vul/phpcodz/blob/master/research/pch-013.md).

You can put your script under a folder named `src`, and run with

```bash
docker-compose up
```

The configuration file path is `/usr/local/etc/php/conf.d/` with `php` as `session.serialize_handler`, and you can see your session file under `/tmp` by default.

If needed, you can edit the `php.ini` file under `config` directory.