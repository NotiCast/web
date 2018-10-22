from flask import Blueprint
from .app_view import AppRouteView

blueprint = Blueprint("docs", __name__, url_prefix="/docs")


class Index(AppRouteView):
    template_name = "docs/index.html"


class DocsPage(AppRouteView):
    def populate(self, page):
        self.template_name = "docs/%s.html" % page
        return {}


blueprint.add_url_rule("/", view_func=Index.as_view("index"))
blueprint.add_url_rule("/<page>", view_func=DocsPage.as_view("page"))


def init_app(app):
    @app.context_processor
    def load_docs_pages():
        return dict(docs_pages=["examples", "web"])
