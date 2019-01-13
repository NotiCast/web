import os

from werkzeug.contrib.fixers import ProxyFix
from raven.contrib.flask import Sentry
from flask import Flask, render_template, request, redirect, g, jsonify
import gigaspoon as gs


def create_app(test_config: dict = None) -> Flask:
    app = Flask(__name__)

    # for usage with proxies
    app.wsgi_app = ProxyFix(app.wsgi_app)

    # sentry = Sentry(app)
    Sentry(app)

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

    for item in ["SQLALCHEMY_DATABASE_URI"]:
        value = os.environ.get(item)
        if value is None:
            print("No config for: %s" % item)
            continue
        elif value.lower() in ("true", "false"):
            app.config[item] = value == "true"
        elif value[:7] == "FORMAT:":
            app.config[item] = value[7:].format(**values)
        else:
            app.config[item] = value

    print(os.environ)
    print(app.config)

    # Ensure the instance exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # extensions
    from .app_view import AppRouteView, response, is_json
    from . import auth, device, docs, group, models
    for item in [auth, device, docs, group, models]:
        if getattr(item, "init_app", None) is not None:
            item.init_app(app)
        if getattr(item, "blueprint", None) is not None:
            app.register_blueprint(item.blueprint)

    from .iot_util import miniarn
    app.jinja_env.filters["miniarn"] = miniarn

    @app.context_processor
    def inject_miniarn():
        return dict(miniarn=miniarn)

    if app.config["ENV"] == "production":
        # in dev mode, do not enforce HTTPS, as domains are local
        @app.before_request
        def redirect_insecure():
            if not request.is_secure:
                return redirect(request.url.replace("http://", "https://"))

    @app.errorhandler(403)
    def not_authorized(e):
        return render_template("errors/_403.html"), 403

    @app.errorhandler(gs.e.FormError)
    def form_error(e):
        status_code = 400
        value = response("Error for form submission (%s)" % e,
                         payload={"type": str(type(e)), "msg": repr(e)},
                         status_code=status_code)
        if is_json(request):
            return jsonify(value), status_code
        return redirect(request.url_rule.rule)

    class Index(AppRouteView):
        template_name = "index.html"

        def populate(self):
            if g.user is not None:
                query = models.Device.query
                devices = query.filter_by(client_id=g.user.client_id).all()
                return {"devices": sorted(
                    [{"name": d.name, "arn": d.arn} for d in devices],
                    key=lambda x: x["name"])}
            return {}

    app.add_url_rule("/", view_func=Index.as_view("index"))

    return app
