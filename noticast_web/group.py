import uuid

import spudbucket as sb

from flask import Blueprint, render_template, session, redirect, url_for, flash
from .iot_util import ThingGroup
from .auth import login_required
from .models import Group, Device, db

blueprint = Blueprint('group', __name__, url_prefix="/group")


# Register new device with AWS and attach to database
@blueprint.route("/", methods=("GET", "POST"))
@login_required
@sb.validator(sb.v.LengthValidator("name_or_arn", min=4))
@sb.validator(sb.v.SelectValidator("group_type", ["arn", "name"]))
@sb.base
def index(form):
    if form.is_form_mode():
        if form["group_type"] == "arn":
            # pull info from IoT Core
            thinggroup = ThingGroup(form["name_or_arn"], "")
            thinggroup.sync()
            group = Group(arn=thinggroup.arn,
                          client_id=session["client_id"],
                          name=thinggroup.name)
            for thing in thinggroup.things:
                device = Device.query.filter_by(arn=thing.arn).first()
                if device is not None:
                    group.devices.append(device)
            db.session.add(group)
            db.session.commit()
        else:
            new_uuid = uuid.uuid4()
            thinggroup = ThingGroup('', new_uuid.hex)
            thinggroup.sync(create=True)
            group = Group(arn=thinggroup.arn,
                          client_id=session["client_id"],
                          name=form["name_or_arn"])
            db.session.add(group)
            db.session.commit()
        return redirect(url_for("group.index"))
    groups = Group.query.filter_by(client_id=session["client_id"]).all()
    return render_template("group/index.html", groups=groups)


@blueprint.route("/manage/<arn>", methods=("GET", "POST"))
@login_required
@sb.base
def manage(form, arn):
    query = [Group.arn.endswith(arn), Group.client_id == session["client_id"]]
    group = Group.query.filter(*query).first()
    devices = Device.query.filter_by(client_id=session["client_id"]).all()
    if form.is_form_mode():
        # query for current devices in group
        client_devices = Device.query.filter_by(client_id=session["client_id"])
        group_devices = client_devices.filter(Device.groups.any(
            Group.arn.endswith(arn))).all()
        for device in group_devices:
            if form.get("dev_" + device.name) is None:
                # remove from database
                group.devices.remove(device)
        for device in devices:
            if (form.get("dev_" + device.name) is None and
                    device not in group.devices):
                group.devices.append(device)
        db.session.commit()
        flash("Successfully updated devices for group|success", "notification")
        flash("Successfully updated devices for group|success", "notification")
        return redirect(url_for("group.manage", arn=arn))

    devices_list = {}
    for device in devices:
        if devices_list.get(device.arn) is None:
            devices_list[device.arn] = (device, False)
        for group in device.groups:
            is_in_group = group.arn[-len(arn):] == arn
            devices_list[device.arn] = (device, is_in_group)
            if is_in_group:
                break
    return render_template("group/manage.html", devices=devices_list,
                           group=group, arn=arn)
