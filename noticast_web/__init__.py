import os

from flask import Flask, render_template, g, session


def create_app(test_config: dict = None) -> Flask:
    app = Flask(__name__)

    # Load environ variables from app file if exists
    try:
        with open("/app/config.env") as f:
            for key, value in (line.split("=") for line in f if "=" in line):
                os.environ[key.strip()] = value.strip().strip("'\"")
    except OSError:
        pass

    # Load project config or testing config
    if test_config is not None:
        app.config.from_mapping(test_config)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

    values = {
        "instance": app.instance_path
    }

    for item in ["SECRET_KEY", "DEBUG", "SQLALCHEMY_DATABASE_URI"]:
        value = os.environ.get(item)
        if value is None:
            print("No config for: %s" % item)
            continue
        elif value in ("true", "false"):
            app.config[item] = value == "true"
        elif value[:7] == "FORMAT:":
            app.config[item] = value[7:].format(**values)
        else:
            app.config[item] = value

    # Ensure the instance exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # extensions
    from . import models
    models.init_app(app)

    # blueprints
    from . import auth, device, group
    app.register_blueprint(auth.blueprint)
    app.register_blueprint(device.blueprint)
    app.register_blueprint(group.blueprint)

    @app.errorhandler(403)
    def not_authorized(e):
        print(e)
        return render_template("errors/_403.html")

    @app.route("/")
    def index():
        if session.get("client_id"):
            query = models.Device.query
            devices = query.filter_by(client_id=session["client_id"]).all()
            return render_template("index.html", devices=devices)
        return render_template("index.html")

    return app
