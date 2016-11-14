#!/bin/bash

# set -ex

#!! Add yourself to cluster-admin before upgrading!!
# oadm policy add-cluster-role-to-user cluster-admin xiazhao@redhat.com
export proj=logging

# oc delete template logging-deployer-account-template logging-deployer-template

oc create -f https://raw.githubusercontent.com/openshift/origin-aggregated-logging/master/deployer/deployer.yaml

oc new-app logging-deployer-account-template



#oc edit template logging-deployer-template -o yaml
#changed from
# image: ${IMAGE_PREFIX}logging-deployment:${IMAGE_VERSION}
#into 
# image: ${IMAGE_PREFIX}logging-deployer:${IMAGE_VERSION}
#
#oc get template logging-deployer-template -o yaml -n logging | sed  's/\(image:\s.*\)logging-deployer\(.*\)/\1logging-deployment\2/g' | oc apply -n logging -f -

oc get template logging-deployer-template -o yaml -n logging | sed  's/\(image:\s.*\)logging-deployment\(.*\)/\1logging-deployer\2/g' | oc apply -n logging -f -

oc policy add-role-to-user edit --serviceaccount logging-deployer
oc policy add-role-to-user daemonset-admin --serviceaccount logging-deployer
oadm policy add-cluster-role-to-user oauth-editor system:serviceaccount:logging:logging-deployer

#new step upgraded to 3.4.0
oadm policy add-cluster-role-to-user rolebinding-reader system:serviceaccount:logging:aggregated-logging-elasticsearch


#Upgrade from 3.2.0 where configmap didn't exist
#oc new-app logging-deployer-template -p PUBLIC_MASTER_URL=https://10.8.175.190:8443,ENABLE_OPS_CLUSTER=false,IMAGE_PREFIX=brew-pulp-docker01.web.prod.ext.phx2.redhat.com:8888/openshift3/,IMAGE_VERSION=3.3.1,ES_INSTANCE_RAM=1G,ES_CLUSTER_SIZE=1,KIBANA_HOSTNAME=kibana.1020-37t.qe.rhcloud.com,KIBANA_OPS_HOSTNAME=kibana-ops.1020-37t.qe.rhcloud.com,MASTER_URL=https://10.8.175.190:8443,MODE=upgrade

#Upgrade from 3.3 where configmap exist
oc new-app logging-deployer-template -p IMAGE_PREFIX=brew-pulp-docker01.web.prod.ext.phx2.redhat.com:8888/openshift3/,IMAGE_VERSION=3.4.0,MODE=upgrade










