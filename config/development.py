# Flask
DEBUG = True
TESTING = True
SECRET_KEY = "dev" * 8

# SQLAlchemy
SQLALCHEMY_DATABASE_URI = "sqlite:///instance/noticast.sqlite"
SQLALCHEMY_TRACK_MODIFICATIONS = False
