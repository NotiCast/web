import os

from werkzeug.contrib.fixers import ProxyFix
# from raven.contrib.flask import Sentry  # XXX readd
from flask import Flask, render_template, request, redirect, flash, g
import spudbucket as sb


def create_app(test_config: dict = None) -> Flask:
    app = Flask(__name__)

    # for usage with proxies
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # sentry = Sentry(app)  # XXX readd

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
    from .app_view import AppRouteView
    from . import models
    models.init_app(app)

    # blueprints
    from . import auth, device, group
    app.register_blueprint(auth.blueprint)
    app.register_blueprint(device.blueprint)
    app.register_blueprint(group.blueprint)

    """
    @app.before_request
    def redirect_insecure():
        if not request.is_secure:
            return redirect(request.url.replace('http://', 'https://'))
    """

    @app.errorhandler(403)
    def not_authorized(e):
        return render_template("errors/_403.html")

    @app.errorhandler(sb.e.FormError)
    def form_error(e):
        flash("Error for form submission %s|danger" % e,
              "notification")
        return redirect(request.url_rule.rule)

    class Index(AppRouteView):
        template_name = "index.html"

        def populate(self):
            if g.user is not None:
                query = models.Device.query
                devices = query.filter_by(client_id=g.user.client_id).all()
                return {"devices": [{"name": d.name, "arn": d.arn}
                                    for d in devices]}
            return {}

    app.add_url_rule("/", view_func=Index.as_view("index"))

    return app
