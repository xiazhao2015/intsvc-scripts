#!/bin/bash

curl -o metrics.yaml https://raw.githubusercontent.com/openshift/origin-metrics/enterprise/metrics.yaml
 
#PREFIX=brew-pulp-docker01.web.prod.ext.phx2.redhat.com:8888/openshift3/ 
#PREFIX=registry.ops.openshift.com/openshift3/
#PREFIX=registry.access.stage.redhat.com/openshift3/
PREFIX=registry.access.stage.redhat.com/openshift3/ose-
SUBDOMAIN=`grep subd /etc/origin/master/master-config.yaml | awk '{ print $2 }' | sed 's:^.\(.*\).$:\1:'`
MASTERURL=`grep masterURL /etc/origin/master/master-config.yaml | awk '{ print $2 }'`
 
oc project openshift-infra
 
oc create -f - <<API
apiVersion: v1
kind: ServiceAccount
metadata:
  name: metrics-deployer
secrets:
- name: metrics-deployer
API
 
oadm policy add-role-to-user edit system:serviceaccount:openshift-infra:metrics-deployer
 
oc secrets new metrics-deployer nothing=/dev/null
 
oadm policy add-cluster-role-to-user cluster-reader system:serviceaccount:openshift-infra:heapster
 
oadm policy add-role-to-user view system:serviceaccount:openshift-infra:hawkular -n openshift-infra
 
oc new-app metrics-deployer-template --as=system:serviceaccount:openshift-infra:metrics-deployer \
-p IMAGE_PREFIX=$PREFIX \
-p IMAGE_VERSION=3.4.1 \
-p HAWKULAR_METRICS_HOSTNAME=hawkular-metrics.$SUBDOMAIN \
-p MODE=deploy \
-p USE_PERSISTENT_STORAGE=false \
-p DYNAMICALLY_PROVISION_STORAGE=false \
-p CASSANDRA_NODES=1 \
-p CASSANDRA_PV_SIZE=10Gi \
-p USER_WRITE_ACCESS=false



#-p MASTER_URL=$MASTERURL \
