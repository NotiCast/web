import spudbucket as sb

from flask import Blueprint, render_template, session, redirect, url_for, flash
from .auth import login_required
from .iot_util import get_things
from .models import Device, db

blueprint = Blueprint('device', __name__, url_prefix="/device")


# Register new device with AWS and attach to database
@blueprint.route("/register", methods=("GET", "POST"))
@login_required
@sb.validator(sb.v.LengthValidator("device_name", min=8))
@sb.base
def register(form):
    if form.is_form_mode():
        name = form["device_name"]
        # use a genexpr here because filter(x, lambda y: z) is slower
        for thing in (thing for thing in get_things()
                      if thing.name == name):
            thing.sync()
            device = Device(arn=thing.arn,
                            client_id=session["client_id"],
                            name=thing.name)
            db.session.add(device)
            db.session.commit()
            return redirect(url_for('index'))
        else:
            flash("Device was not found: %r|danger" % name, "notification")
            return redirect(url_for('device.from_arn'))
    return render_template("device/register.html")


# Get new device from AWS, sync, and attach to database
@blueprint.route("/from_arn", methods=("GET", "POST"))
@login_required
@sb.validator(sb.v.ExistsValidator("device_arn"))
@sb.base
def from_arn(form):
    if form.is_form_mode():
        arn = form["device_arn"]
        # use a genexpr here because filter(x, lambda y: z) is slower
        for thing in (thing for thing in get_things() if thing.arn == arn):
            if thing.arn == arn:
                thing.sync()
                device = Device(arn=arn,
                                client_id=session["client_id"],
                                name=thing.name)
                db.session.add(device)
                db.session.commit()
            return redirect(url_for('index'))
        else:
            flash("Device was not found: %r|danger" % arn, "notification")
            return redirect(url_for('device.from_arn'))
    return render_template("device/from_arn.html")
