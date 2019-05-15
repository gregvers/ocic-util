#!/bin/bash

# usage example:
# ./image.sh --env-file=file.env --machinename=myimage --object=file.tgz

## arguments retrieval
for i in "$@"
do
  case $i in
    --env-file=*)
      ENVFILE="${i#*=}"
      ;;
    --imagename=*)
      IMAGENAME="${i#*=}"
      ;;
    --object=*)
      OBJECT="${i#*=}"
      ;;
    *)
      echo Error: Unknow argument
      exit
      ;;
  esac
done
if [[ ! $ENVFILE || ! $IMAGENAME || ! $OBJECT ]] ; then
  echo "Error: missing arguments"
  echo "Syntax: "
  echo "image.sh arguments"
  echo "arguments:"
  echo "  --env-file=<envfile absolute path and name>   example: /tmp/myenv.env"
  echo "  --image=<instance>    example: /Compute-500011111/user@domain.com/myOL7"
  echo "  --object=<objectname in compute-image container in Cloud Storage>   example: myOL7.tgz"
  echo "the envfile contains the values for USER, PASSWORD, IDENTITY_DOMAIN, STORAGE_DOMAIN, COMPUTE_ENDPOINT, STORAGE_ENDPOINT in the following format:"
  echo "USER=user@domain.com"
  echo "PASSWORD=xxxxxx"
  echo "IDENTITY_DOMAIN=500011111"
  echo "COMPUTE_ENDPOINT=https://compute.us1.ocm.s1234567.oraclecloudatcustomer.com"
  echo "STORAGE_ENDPOINT=https://storageaccountname.us1.ocm.s1234567.oraclecloudatcustomer.com"
  exit
fi

## check dependencies
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
if [ "$COMPUTE_ENDPOINT" == "" ]; then
  echo "Compute API endpoint is not specified!"
  exit
fi
if [ "$STORAGE_ENDPOINT" == "" ]; then
  echo "Storage API endpoint is not specified!"
  exit
fi

echo -e "Authenticating with Compute..."
curl -ks -c compute-cookie -H "Accept:application/json" -H "Content-Type: application/json" \
  $COMPUTE_ENDPOINT/authenticate/  \
  -d "{\"user\":\"Compute-$IDENTITY_DOMAIN/$USER\",\"password\":\"$PASSWORD\"}"

echo -e "\nCreating machine image..."
curl -X POST \
  $COMPUTE_ENDPOINT/machineimage/ \
  -H 'Content-Type: application/oracle-compute-v3+json' \
  -H 'Accept: application/oracle-compute-v3+json' \
  -b compute-cookie \
  -d "{
	\"name\": \"/Compute-$IDENTITY_DOMAIN/$USER/$IMAGENAME\",
	\"sizes\": {\"total\":0},
	\"no_upload\": true,
	\"account\": \"/Compute-$IDENTITY_DOMAIN/cloud_storage\",
	\"file\": \"$OBJECT\",
	\"platform\": \"windows\"
  }"

echo -e "\nCreating image list..."
curl -X POST \
  $COMPUTE_ENDPOINT/imagelist/ \
  -H 'Accept: application/oracle-compute-v3+json' \
  -H 'Content-Type: application/oracle-compute-v3+json' \
  -b compute-cookie \
  -d "{
        \"name\": \"/Compute-orcdevtest1/gregory.verstraeten@oracle.com/$IMAGENAME\",
        \"description\": \"$IMAGENAME\"
  }"

echo -e "\nCreating image list entry..."
curl -X POST \
  $COMPUTE_ENDPOINT/imagelist/Compute-$IDENTITY_DOMAIN/$USER/$IMAGENAME/entry/ \
  -H 'Accept: application/oracle-compute-v3+json' \
  -H 'Content-Type: application/oracle-compute-v3+json' \
  -b compute-cookie \
  -d "{
        \"machineimages\": [\"/Compute-$IDENTITY_DOMAIN/$USER/$IMAGENAME\"],
        \"version\": 1
  }"

echo -e "\n"