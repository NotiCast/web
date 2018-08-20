import functools

import gigaspoon as gs
from flask import (
    Blueprint, g, abort, request, redirect, session, url_for, flash
)
from werkzeug import check_password_hash, generate_password_hash
from .app_view import AppRouteView, response
from .models import IntegrityError, User, Client, db

blueprint = Blueprint("auth", __name__, url_prefix="/auth")


class Register(AppRouteView):
    decorators = [
        gs.validator(gs.v.SelectValidator("i-am", ["user", "client"])),
        gs.validator(gs.v.LengthValidator("username", min=5, max=30)),
        gs.validator(gs.v.LengthValidator("password", min=7))
    ]
    route = "auth.register"
    template_name = "auth/register.html"

    def handle_post(self, values):
        self.redirect_to = "auth.login"  # redirect to login on success
        username = values["username"]
        password = values["password"]
        if values["i-am"] == "user":
            client_username = values["client_username"]
            client_id = User.query.filter(User.username.like(
                client_username)).first().client_id
        elif values["i-am"] == "client":
            client = Client()
            db.session.add(client)
            db.session.commit()
            client_id = client.id
        try:
            user = User(client_id=client_id,
                        username=username,
                        password=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
        except IntegrityError as err:
            self.redirect_to = self.route
            return response("User already exists: %s" % username, 409)


blueprint.add_url_rule("/register", view_func=Register.as_view("register"))


def check_login(password, username: str = None, user: User = None):
    if username is None and user is None:
        raise ValueError("expected `username` or `user`")
    if username is not None and user is not None:
        raise ValueError("expected exactly one of [`username`, `user`]")
    if user is None:
        user = User.query.filter(User.username.like(username)).first()
    if user is not None:
        if check_password_hash(user.password, password):
            return user
    return None


class Login(AppRouteView):
    decorators = [
        gs.validator(gs.v.ExistsValidator("username")),
        gs.validator(gs.v.ExistsValidator("password"))
    ]
    route = "auth.login"
    template_name = "auth/login.html"

    def handle_post(self, values):
        self.redirect_to = "index"  # redirect to index on success
        username = values["username"]

        user = check_login(values["password"], username=username)
        if user is None:
            self.redirect_to = self.route
            return response("Username or password incorrect", 401)

        session.clear()
        session["user_id"] = user.id
        session["client_id"] = user.client_id


blueprint.add_url_rule("/login", view_func=Login.as_view("login"))


@blueprint.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@blueprint.before_app_request
def load_user():
    user = None
    user_id = session.get("user_id")
    if user_id is None:
        auth_header = request.headers.get("Authorization")
        if auth_header is not None:
            username, pw = auth_header.split(" ")[-1].split(":")
            user = check_login(pw, username=username)
    else:
        user = User.query.filter_by(id=user_id).first()
        if user is None:
            flash("Expected user by id: %i; contact support|danger" % user_id,
                  "notifications")
    g.user = user


def login_required(fn):
    @functools.wraps(fn)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return abort(403)
        return fn(*args, **kwargs)
    return wrapped_view


def admin_required(fn):
    @functools.wraps(fn)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return abort(403)
        if not g.user.client.is_admin:
            return abort(403)
        return fn(*args, **kwargs)
    return wrapped_view
