import os

from flask import Flask, render_template, g, session


def create_app(test_config: dict = None) -> Flask:
    app = Flask(__name__)

    # Load project config or testing config
    if test_config is not None:
        app.config.from_mapping(test_config)

    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

    vars = {
        "instance": app.instance_path
    }

    for item in ["SECRET_KEY", "DEBUG", "SQLALCHEMY_DATABASE_URI"]:
        value = os.environ.get(item)
        if value is None:
            print("No config for: %s" % item)
            continue
        elif value in ("true", "false"):
            app.config[item] = value == "true"
        else:
            app.config[item] = value.format(vars)

    print(app.secret_key)

    # Ensure the instance exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # extensions
    from . import models
    models.init_app(app)

    # blueprints
    from . import auth, device
    app.register_blueprint(auth.blueprint)
    app.register_blueprint(device.blueprint)

    @app.route("/")
    def index():
        if session.get("client_id"):
            query = models.Device.query
            devices = query.filter_by(client_id=session["client_id"]).all()
            return render_template("index.html", devices=devices)
        return render_template("index.html")

    return app
