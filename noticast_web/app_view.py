from flask import flash, jsonify, redirect, render_template, request, url_for
from flask.views import MethodView

# Avoid recreating for every request (despite immutability...?)
VALID_HEADERS = ["application/json", "text/html"]


def is_json(request):
    header = request.accept_mimetypes.best_match(VALID_HEADERS)
    return header == VALID_HEADERS[0]


def response(message: str, status_code: int = 200,
             category: str = None, payload: dict = None):
    if is_json(request):
        if payload is not None:
            # return payload
            return {
                "payload": payload,
                "status_code": status_code
            }
        else:
            return {
                "message": message,
                "status_code": status_code
            }
    if category is None:
        category = "success"
        if status_code >= 500:
            category = "danger"
        elif status_code >= 400:
            category = "warning"
    flash("%s|%s" % (message, category), "notification")
    return {}


class AppRouteView(MethodView):
    headers = ["application/json", "text/html"]
    redirect_to = None
    redirect_args = {}

    def get_template_name(self):
        # Override
        return self.template_name

    def render_template(self, **context):
        return render_template(self.get_template_name(), **context)

    # POST requests
    # All HTTP POST requests should redirect to avoid refresh-duplication, so
    # do not overwrite post_html without a redirect

    def handle_post(self, values, *args, **kwargs) -> dict:
        """
        Must return a dict.
        Dict Formats:
        {
            "payload": <JSON serializable content>[,
            "status_code": <HTTP status number>]
        }
        {
            "message": "one-liner for quick output"[,
            "status_code": <HTTP status number>]
        }
        """
        raise NotImplementedError()

    def post_json(self, *args, **kwargs):
        values = request.json
        result = self.handle_post(values, *args, **kwargs)
        if "payload" in result:
            return jsonify(result["payload"]), result.get("status_code", 200)
        return (jsonify({"message": result.get("message", "no output")}),
                result.get("status_code", 200))

    def post_html(self, *args, **kwargs):
        values = request.form
        self.handle_post(values, *args, **kwargs)
        if self.redirect_to is not None:
            return redirect(url_for(self.redirect_to, **self.redirect_args))
        return redirect(url_for(self.route, **self.redirect_args))

    # GET requests

    def populate(self, *args, **kwargs):
        # Override
        return {}

    def get_json(self, *args, **kwargs):
        values = self.populate(*args, **kwargs)
        return jsonify(values), values.get("status_code", 200)

    def get_html(self, *args, **kwargs):
        return self.render_template(**self.populate(*args, **kwargs))

    # MethodView overrides

    def get(self, *args, **kwargs):
        if is_json(request):
            return self.get_json(*args, **kwargs)
        return self.get_html(*args, **kwargs)

    def post(self, *args, **kwargs):
        if is_json(request):
            return self.post_json(*args, **kwargs)
        else:
            return self.post_html(*args, **kwargs)
