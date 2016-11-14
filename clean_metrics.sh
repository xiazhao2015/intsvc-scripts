#!/bin/bash

oc delete all,secrets,sa,templates --selector=metrics-infra -n openshift-infra
oc delete sa,secret metrics-deployer -n openshift-infra
