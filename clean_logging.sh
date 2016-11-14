#!/bin/bash

oc delete sa aggregated-logging-kibana aggregated-logging-elasticsearch aggregated-logging-fluentd aggregated-logging-curator logging-deployer
oc delete clusterrole oauth-editor daemonset-admin rolebinding-reader
oc delete rolebinding logging-deployer-edit-role logging-deployer-dsadmin-role logging-elasticsearch-view-role
oc delete secrets logging-deployer
oc delete configmap logging-deployer
oc delete pods --all
oc delete is --all
oc delete dc --all
oc delete rc --all
oc delete svc --all
