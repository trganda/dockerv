#!/bin/bash

# Wait for heathy ElasticSearch
# next wait for ES status to turn to Green
health_check="$(curl -fsSL "${UNOMI_ELASTICSEARCH_ADDRESSES}/_cat/health?h=status")"

until ([ "$health_check" = 'yellow' ] || [ "$health_check" = 'green' ]); do
    health_check="$(curl -fsSL "${UNOMI_ELASTICSEARCH_ADDRESSES}/_cat/health?h=status")"
    >&2 echo "Elastic Search is unavailable - waiting"
    sleep 1
done

# start karaf background
/opt/unomi-1.5.0/bin/start

KARAF_STATUS=`/opt/unomi-1.5.0/bin/status`
RET=$(echo $KARAF_STATUS | grep "Not Running")
while [[ "$RET" == "1" ]]
do
    sleep 2
    KARAF_STATUS=`/opt/unomi-1.5.0/bin/status`
    RET=$(echo $KARAF_STATUS | grep "Not Running")
done
KARAF_STATUS=`/opt/unomi-1.5.0/bin/status`
echo $KARAF_STATUS

tail -f /opt/unomi-1.5.0/data/log/karaf.log
