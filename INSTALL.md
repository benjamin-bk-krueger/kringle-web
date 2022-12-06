# Installation

## Docker container

Kringle.info can be run fully containerized. You will need at least the following files:

* docker-compose.yml - Docker compose file (see GIT repo)
* db/init.sql - Database initialization script (see GIT repo)
* .aws/config - AWS client configuration (see sample below)
* .aws/credentials - AWS client credentials (see sample below)

```
C:\Temp\kringle>type .aws\config
[default]
region = eu-central-1
```

```
C:\Temp\kringle>type .aws\credentials
[default]
aws_access_key_id = minio_access_key
aws_secret_access_key = minio_secret_key
```

Just run a docker compose:

![Docker compose 1](https://github.com/benjamin-bk-krueger/kringle-web/blob/main/install1.png?raw=true)

As soon as all images have been downloaded and all containers are up and running, you can log into the application by navigating to http://127.0.0.1:5010/web/.  
You can create a first user using the invitation code "heureka".

![Docker compose 2](https://github.com/benjamin-bk-krueger/kringle-web/blob/main/install2.png?raw=true)

## Fully self-hosted


TBD.   
