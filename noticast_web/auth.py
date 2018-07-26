import functools

import spudbucket as sb
from flask import (
    Blueprint, g, abort, redirect, render_template, request, session, url_for,
    flash
)
from werkzeug import check_password_hash, generate_password_hash
from .models import User, Client, db

blueprint = Blueprint("auth", __name__, url_prefix="/auth")


@blueprint.route("/register", methods=("GET", "POST"))
@sb.validator(sb.v.ExistsValidator("i-am"))
@sb.validator(sb.v.LengthValidator("username", min=5, max=30))
@sb.validator(sb.v.LengthValidator("password", min=7))
@sb.base
def register(form):
    if form.is_form_mode():
        username = form["username"]
        password = form["password"]
        if form["i-am"] == "user":
            client_username = request.form["client_username"]
            client_id = User.query.filter(User.username.like(
                client_username)).first().client_id
        elif form["i-am"] == "client":
            client = Client()
            db.session.add(client)
            db.session.commit()
            client_id = client.id
        else:
            raise ValueError(form["i-am"])
        user = User(client_id=client_id,
                    username=username,
                    password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('auth.login'))
    return render_template("auth/register.html")


@blueprint.route("/login", methods=("GET", "POST"))
@sb.validator(sb.v.ExistsValidator("username"))
@sb.validator(sb.v.ExistsValidator("password"))
@sb.base
def login(form):
    if form.is_form_mode():
        username = request.form["username"]
        user = User.query.filter(User.username.like(username)).first()

        if not check_password_hash(user.password, request.form["password"]):
            flash("Password incorrect for: %s|danger" % user.username,
                  "notification")
            return render_template("auth/login.html"), 404

        session.clear()
        session["user_id"] = user.id
        session["client_id"] = user.client_id
        return redirect(url_for("index"))
    return render_template("auth/login.html")


@blueprint.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@blueprint.before_app_request
def load_user():
    user_id = session.get("user_id")
    if user_id is None:
        g.user = None
    else:
        g.user = User.query.filter_by(id=user_id).first()


def login_required(fn):
    @functools.wraps(fn)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            return abort(403)
        return fn(*args, **kwargs)
    return wrapped_view
