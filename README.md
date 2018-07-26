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
