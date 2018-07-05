import spudbucket as sb

from flask import Blueprint, render_template
from .auth import login_required

blueprint = Blueprint('device', __name__, url_prefix="/device")


@blueprint.route("/register", methods=("GET", "POST"))
@login_required
@sb.validator(sb.v.LengthValidator("device_name", min=8))
@sb.base
def register(form):
    if form.is_form_mode():
        return 'heeeyyyyy'
    return render_template("device/register.html")


@blueprint.route("/from_arn", methods=("GET", "POST"))
@login_required
@sb.validator(sb.v.ExistsValidator("device_arn"))
@sb.base
def from_arn(form):
    if form.is_form_mode():
        return 'heeeyyyyy'
    return render_template("device/from_arn.html")
