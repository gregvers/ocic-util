#!/bin/bash

# source the Oracle Cloud Account info
. ./env.sh

# Authentication
echo Authentication...
export AUTHTOKEN=`curl -v -X GET \
	-H "X-Storage-User: Storage-"$IDENTITYDOMAIN":"$USER \
	-H "X-Storage-Pass: "$PASSWORD \
	$STORAGE_ENDPOINT/auth/v1.0 \
	2>&1 | grep "X-Auth-Token: " | awk '{print $3}'`
echo Authentication token is $AUTHTOKEN

# Create container
echo Create container...
curl -v -X PUT \
	-H "X-Auth-Token: $AUTHTOKEN" \
	$STORAGE_ENDPOINT/demo

# Set permission on the container
echo Set permission on container...
curl -v -X POST \
     -H "X-Auth-Token: $AUTHTOKEN" \
     -H "X-Container-Read: .r:*,.rlistings" \
     $STORAGE_ENDPOINT/demo

# Upload cookbooks.zip
curl -v -X PUT \
	-H "X-Auth-Token: $AUTHTOKEN" \
	-T  ./artifacts/cookbooks.zip \
	$STORAGE_ENDPOINT/demo/cookbooks.zip

# Upload nginx.conf
echo Upload nginx.conf...
curl -v -X PUT \
	-H "X-Auth-Token: $AUTHTOKEN" \
	-T  ./artifacts/nginx.conf \
	$STORAGE_ENDPOINT/demo/nginx.conf

# Upload simpleapp.js
echo Upload simpleapp.js...
curl -v -X PUT \
	-H "X-Auth-Token: $AUTHTOKEN" \
	-T  ./artifacts/simpleapp.js \
	$STORAGE_ENDPOINT/demo/simpleapp.js

# Upload simpleapp
echo Upload simpleapp...
curl -v -X PUT \
	-H "X-Auth-Token: $AUTHTOKEN" \
	-T  ./artifacts/simpleapp \
	$STORAGE_ENDPOINT/demo/simpleapp

# List content of container with authentication
echo List content of container with authentication...
curl -X GET \
	-H "X-Auth-Token: $AUTHTOKEN" \
	$STORAGE_ENDPOINT/demo

# List content of container without authentication
echo List content of container without authentication...
curl $STORAGE_ENDPOINT/demo
