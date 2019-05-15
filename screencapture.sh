#!/bin/bash

# usage example:
# ./screencapture.sh --env-file=file.env --instance=/account/user/id

## arguments retrieval
for i in "$@"
do
  case $i in
    --env-file=*)
      ENVFILE="${i#*=}"
      ;;
    --instance=*)
      INSTANCE="${i#*=}"
      ;;
    *)
      echo Error: Unknow argument
      exit
      ;;
  esac
done
if [[ ! $ENVFILE || ! $INSTANCE ]] ; then
  echo "Error: missing arguments"
  echo "Syntax: "
  echo "screencapture.sh arguments"
  echo "arguments:"
  echo "  --env-file=<envfile absolute path and name>   example: /tmp/myenv.env"
  echo "  --instance=<instance>    example: /Compute-500011111/user@domain.com/6f1dd5da-77ed-41ed-b824-df28477be2a2"
  echo "the envfile contains the values for USER, PASSWORD, IDENTITY_DOMAIN, STORAGE_DOMAIN, COMPUTE_ENDPOINT, STORAGE_ENDPOINT in the following format:"
  echo "USER=user@domain.com"
  echo "PASSWORD=xxxxxx"
  echo "IDENTITY_DOMAIN=500011111"
  echo "STORAGE_DOMAIN=storageaccountname"
  echo "COMPUTE_ENDPOINT=https://compute.us1.ocm.s1234567.oraclecloudatcustomer.com"
  echo "STORAGE_ENDPOINT=https://storageaccountname.us1.ocm.s1234567.oraclecloudatcustomer.com"
  exit
fi

## check dependencies
if [ ! $(which jq) ]; then
  echo "jq command not found!"
  exit
fi
if [ ! $(which curl) ]; then
  echo "curl command not found!"
  exit
fi

## check environment variables
if [ ! -f $ENVFILE ]; then
  echo "Environment file $ENVFILE not found!"
  exit
fi
. $ENVFILE

if [ "$USER" == "" ]; then
  echo "Cloud User is not specified!"
  exit
fi
if [ "$PASSWORD" == "" ]; then
  echo "Cloud User password is not specified!"
  exit
fi
if [ "$IDENTITY_DOMAIN" == "" ]; then
  echo "Identity Domain is not specified!"
  exit
fi
if [ "$STORAGE_DOMAIN" == "" ]; then
  echo "Storage Domain is not specified!"
  exit
fi
if [ "$COMPUTE_ENDPOINT" == "" ]; then
  echo "Compute API endpoint is not specified!"
  exit
fi
if [ "$STORAGE_ENDPOINT" == "" ]; then
  echo "Storage API endpoint is not specified!"
  exit
fi

echo Authenticating with Compute...
curl -ks -c cookie -H "Accept:application/json" -H "Content-Type: application/json" \
  $COMPUTE_ENDPOINT/authenticate/  \
  -d "{\"user\":\"Compute-$IDENTITY_DOMAIN/$USER\",\"password\":\"$PASSWORD\"}"

echo Creating the screen capture...
SCREENCAPTURE_URI=$( \
  curl -ks -b cookie -c cookie -H "Accept: application/json" -H "Content-Type: application/json" \
  $COMPUTE_ENDPOINT/compute/v1/console/screencapture/ \
  -d "{\"cancel\": false, \"instance\":\"$INSTANCE\", \"account\": \"/Compute-$IDENTITY_DOMAIN/cloud_storage\"}" \
  -X POST | jq -r '.uri' )
## we look for the "uri" in the form of $COMPUTE_ENDPOINT/compute/v1/console/screencapture/$INSTANCE/20180205-1940"

echo Checking the status of screen capture URI $SCREENCAPTURE_URI...
SCREENCAPTURE_MEDIA_URI=""
while [[ $SCREENCAPTURE_MEDIA_URI = "" ]]; do
  SCREENCAPTURE_MEDIA_URI=$( \
    curl -ks -b cookie -c cookie -H "Accept: application/json" -H "Content-Type: application/json" \
    $SCREENCAPTURE_URI | jq -r '.media_uri' )
  echo waiting for screen capture to be completed.  SCREENCAPTURE_MEDIA_URI=$SCREENCAPTURE_MEDIA_URI
  sleep 5;
done
## we look for the "media_uri": "https://orcdevtest1.storage.oraclecloud.com/v1/Storage-orcdevtest1/compute_images/Compute-orcdevtest1/gregory.verstraeten@oracle.com/jumphost/f4e9d0e0-0cb9-40ff-82e6-1335211e5464/20180205-1751.png"

echo The screen capture image file is located at $SCREENCAPTURE_MEDIA_URI

echo Authenticating with Cloud Storage...
AUTHTOKEN=$( curl -v -X GET \
  -H "X-Storage-User: Storage-"$STORAGE_DOMAIN":"$USER \
  -H "X-Storage-Pass: "$PASSWORD \
  $STORAGE_ENDPOINT/auth/v1.0 \
  2>&1 | grep "X-Auth-Token: " | awk '{print $3}' )

echo Downloading the screen capture image using the media URI to local folder...
curl -X GET -H "X-Auth-Token: $AUTHTOKEN" \
  $SCREENCAPTURE_MEDIA_URI  -o ./screencapture.png
