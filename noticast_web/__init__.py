import os

from flask import Flask, render_template, g, session


def create_app(test_config: dict = None) -> Flask:
    app = Flask(__name__)

    # Load project config or testing config
    if test_config is None:
        stage = os.environ.get("FLASK_ENV", "development")
        app.config.from_pyfile("config/%s.py" % stage)
    else:
        app.config.from_mapping(test_config)

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
