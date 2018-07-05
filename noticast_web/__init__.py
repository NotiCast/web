import os

from flask import Flask, render_template, g


def create_app(test_config: dict = None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    database_path = os.path.join(app.instance_path, "noticast.sqlite")
    app.config.from_mapping(
        SECRET_KEY=("dev" * 8),
        # ::TODO:: Change this
        SQLALCHEMY_DATABASE_URI="sqlite:///%s" % database_path,
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    # Load project config or testing config
    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)

    # Ensure the instance exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    @app.route("/")
    def index():
        print(g.__dict__["user"].username)
        return render_template("index.html")

    # extensions
    from . import models
    models.init_app(app)

    # blueprints
    from . import auth, device
    app.register_blueprint(auth.blueprint)
    app.register_blueprint(device.blueprint)

    return app
