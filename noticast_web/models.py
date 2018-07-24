import click
from flask.cli import with_appcontext

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    users = db.relationship("User", backref="client", lazy=True)
    groups = db.relationship("Group", backref="client", lazy=True)
    devices = db.relationship("Device", backref="client", lazy=True)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"),
                          nullable=False)
    username = db.Column(db.String, nullable=False)
    password = db.Column(db.String, nullable=False)


devices2groups = db.Table(
    "devices2groups",
    db.Column("device_id", db.Integer, db.ForeignKey("device.id"),
              primary_key=True, nullable=False),
    db.Column("group_id", db.Integer, db.ForeignKey("group.id"),
              primary_key=True, nullable=False)
)


class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    arn = db.Column(db.String, unique=True, nullable=False)
    name = db.Column(db.String, unique=False, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"),
                          nullable=False)
    groups = db.relationship("Group", secondary="devices2groups",
                             backref=db.backref("devices"))


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey("client.id"),
                          nullable=False)
    # devices exists in the `groups` backref


@click.command("init-db")
@with_appcontext
def init_db_command():
    """Clear and reset db"""
    db.create_all()
    click.echo("Initialized database")


def init_app(app):
    db.init_app(app)
    app.cli.add_command(init_db_command)
