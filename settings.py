APP_HOST=""
APP_PORT=""

APP_HOST="127.0.0.1"
APP_PORT="8888"

AWS_ACCESS_KEY=""
AWS_BUCKET_NAME=""
AWS_BUCKET_REGION=""
AWS_SECRET_ACCESS=""

AUTH_HEADER_VAL=""

LOCAL_STORAGE_DIR="tempstore"

DB_SETTINGS = {}

try:
    from local_settings import *
except:
    print("No local settings found")
