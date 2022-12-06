# Python venv
export PATH=~/venv/bin:$PATH

# Default credentials, need to be changed on production stage
export POSTGRES_URL=localhost:5432
export POSTGRES_USER=kringle
export POSTGRES_PW=kringle
export POSTGRES_DB=kringle
export SECRET_KEY=secret-key-goes-here
export FLASK_ENV=production
export FLASK_DEBUG=0
export S3_ENDPOINT=http://localhost:9000
export S3_FOLDER=http://localhost:9000/kringle-public
export S3_QUOTA=100
export BUCKET_PUBLIC=kringle-public
export BUCKET_PRIVATE=kringle-private
export WWW_SERVER=http://localhost:5010
export MAIL_ENABLE=1
export MAIL_SERVER=localhost
export MAIL_SENDER=mail@localhost
export MAIL_ADMIN=admin@localhost
export APP_VERSION=1.1
export APP_PREFIX=
