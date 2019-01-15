Flask website for NotiCast device manglement

# Running
```sh
ln -s config.env config.postgres.env
docker-compose up --build
```

# Configuration - `config.env`

- `FLASK_ENV` - One of: "development", "production"
- `FLASK_APP` - Should always be `noticast_web`
- `SECRET_KEY` - 24-byte HMAC key
- `DEBUG` - `true` or `false` depending on debug mode
- `SQLALCHEMY_DATABASE_URI` - SQLAlchemy database URI
- `AWS_DEFAULT_REGION` - AWS region for IoT Core devices
- `AWS_ACCESS_KEY_ID` - Access credentials for IoT Core management
- `AWS_SECRET_ACCESS_KEY` - Secret key for AWS credentials


# Getting everything running

- `git clone --recursive https://github.com/NotiCast/infra`
- `cd infra`
- `terraform init`
- - (supply `us-east-2` as the desired area)
- `make`
-  check if vendor/noticast_web/ansible/vars exists, if not, `mkdir vars` there
- SSH into node[0-2].nodes.uat.noticast.io to make sure they are stored in
the SSH agent
- `make deploy`

At this point, everything should go off correctly. If not, check to make
sure all the required dependencies are installed, that the SSH into the nodes
and servers is working correctly (incorrect passwords, certificates, or keys 
will cause an error/prompt/break everything).

To push a new change to the website, run each of the commands from `make` on.