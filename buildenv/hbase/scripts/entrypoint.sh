#!/bin/bash

WAITSECS=${30:-15}
echo "starting hbase and sleeping ${WAITSECS} seconds for hbase to come online"
/opt/hbase-2.4.8/bin/start_hbase.sh &
sleep ${WAITSECS}
touch /data/hbase/hbase_started

while [ 1 ]
do
    sleep 1
done