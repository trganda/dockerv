## 使用方式

使用此方式配置 MEMOS 是为了能够开启 `https`。

> 以下内容参考了 vietanhdev 的项目 [my-memos](https://github.com/vietanhdev/my-memos)

通过 certbot 获取证书，假设域名为`dev.com`

```sh
certbot certonly --standalone -d dev.com
```

复制证书至当前目录，并修改所有者为当前用户，同时配置为仅当前用户可读

```sh
chown <user> <path>
chmod 400 <path>
```

之后启动 MEMOS

```sh
docker-compose up -d
```
