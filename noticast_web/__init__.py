import os

from flask import Flask, render_template, g, session


def create_app(test_config: dict = None) -> Flask:
    app = Flask(__name__)

    # Load project config or testing config
    if test_config is not None:
        app.config.from_mapping(test_config)

    for item in ["SECRET_KEY", "DEBUG"]:
        value = os.environ[item]
        if value in ("true", "false"):
            app.config[item] = value == "true"
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
