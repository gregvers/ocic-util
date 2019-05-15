curl -X POST https://compute.uscom-central-1.oraclecloud.com/authenticate/ \
  -H "Content-Type: application/oracle-compute-v3+json" \
  -c compute-cookie \
  -d '{ 
    "password": "RBRQv3rCta",
    "user": "/Compute-orcdevtest1/gregory.verstraeten@oracle.com"
  }'

