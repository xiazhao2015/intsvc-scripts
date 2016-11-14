#!/bin/bash

# The real index format:
# /nfs/logging-es/data/logging-es/nodes/0/indices:
# xiazhao.51be5693-7f0a-11e6-a4ea-0efcc55ea7f5.2016.09.20

# The new index format of 3.4.0 should be
# [project.$projectname.$projectuuid.YYYY.mm.dd
# [.operations should still be the same :
# [.operations.YYYY.mm.dd

# to create UUID .$(cat /proc/sys/kernel/random/uuid).2016


oc exec logging-fluentd-nsoi2 -- curl -s --cacert /etc/fluent/keys/ca --cert /etc/fluent/keys/cert --key /etc/fluent/keys/key -XPOST https://logging-es:9200/project.day1.$(cat /proc/sys/kernel/random/uuid).2016.2016.10.26/curatortest/ -d '{
    "message" : "day1 2016.10.26 message"
}'
echo
oc exec logging-fluentd-nsoi2 -- curl -s --cacert /etc/fluent/keys/ca --cert /etc/fluent/keys/cert --key /etc/fluent/keys/key -XPOST https://logging-es:9200/project.week1.$(cat /proc/sys/kernel/random/uuid).2016.2016.10.26/curatortest/ -d '{
    "message" : "week1 2016.10.26 message"
}'
echo
oc exec logging-fluentd-nsoi2 -- curl -s --cacert /etc/fluent/keys/ca --cert /etc/fluent/keys/cert --key /etc/fluent/keys/key -XPOST https://logging-es:9200/project.month1.$(cat /proc/sys/kernel/random/uuid).2016.2016.10.26/curatortest/ -d '{
    "message" : "month1 2016.10.26 message"
}'
echo
oc exec logging-fluentd-nsoi2 -- curl -s --cacert /etc/fluent/keys/ca --cert /etc/fluent/keys/cert --key /etc/fluent/keys/key -XPOST https://logging-es:9200/project.day1-dup.$(cat /proc/sys/kernel/random/uuid).2016.2016.10.26/curatortest/ -d '{
    "message" : "day1-dup 2016.10.26 message"
}'
echo
oc exec logging-fluentd-nsoi2 -- curl -s --cacert /etc/fluent/keys/ca --cert /etc/fluent/keys/cert --key /etc/fluent/keys/key -XPOST https://logging-es:9200/project.day1-tri.$(cat /proc/sys/kernel/random/uuid).2016.2016.10.26/curatortest/ -d '{
    "message" : "day1-tri 2016.10.26 message"
}'

echo
oc exec logging-fluentd-nsoi2 -- curl -s --cacert /etc/fluent/keys/ca --cert /etc/fluent/keys/cert --key /etc/fluent/keys/key -XPOST https://logging-es:9200/project.day1.$(cat /proc/sys/kernel/random/uuid).2016.2016.08.29/curatortest/ -d '{
    "message" : "day1 2016.08.29 message"
}'
echo
oc exec logging-fluentd-nsoi2 -- curl -s --cacert /etc/fluent/keys/ca --cert /etc/fluent/keys/cert --key /etc/fluent/keys/key -XPOST https://logging-es:9200/project.week1.$(cat /proc/sys/kernel/random/uuid).2016.2016.08.15/curatortest/ -d '{
    "message" : "week1 2016.08.15 message"
}'
echo
oc exec logging-fluentd-nsoi2 -- curl -s --cacert /etc/fluent/keys/ca --cert /etc/fluent/keys/cert --key /etc/fluent/keys/key -XPOST https://logging-es:9200/project.month1.$(cat /proc/sys/kernel/random/uuid).2016.2016.06.22/curatortest/ -d '{
    "message" : "month1 2016.06.22 message"
}'
echo

oc exec logging-fluentd-nsoi2 -- curl -s --cacert /etc/fluent/keys/ca --cert /etc/fluent/keys/cert --key /etc/fluent/keys/key -XPOST https://logging-es:9200/project.day1-dup.$(cat /proc/sys/kernel/random/uuid).2016.2016.09.01/curatortest/ -d '{
    "message" : "day1-dup 2016.09.01 message"
}'
echo

oc exec logging-fluentd-nsoi2 -- curl -s --cacert /etc/fluent/keys/ca --cert /etc/fluent/keys/cert --key /etc/fluent/keys/key -XPOST https://logging-es:9200/project.day1-tri.$(cat /proc/sys/kernel/random/uuid).2016.2016.08.29/curatortest/ -d '{
    "message" : "day1-tri 2016.08.23 message"
}'
echo

oc exec logging-curator-1-v4d2g -- curator --host logging-es --use_ssl --certificate /etc/curator/keys/ca --client-cert /etc/curator/keys/cert --client-key /etc/curator/keys/key --loglevel ERROR show indices --all-indices
