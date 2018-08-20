import uuid

import gigaspoon as gs

from flask import (Blueprint, g, request)
from .iot_util import ThingGroup
from .auth import login_required
from .models import Group, Device, db
from .app_view import AppRouteView, response

blueprint = Blueprint('group', __name__, url_prefix="/group")


def transform_group(group):
    return {
        "name": group.name,
        "arn": group.arn,
        "devices": sorted(
            [{"name": d.name, "arn": d.arn} for d in group.devices],
            key=lambda x: x["name"])
    }


class Index(AppRouteView):
    decorators = [
        login_required,
        gs.validator(gs.v.Length("name_or_arn", min=4)),
        gs.validator(gs.v.Select("group_type", ["arn", "name"]))
    ]
    route = "group.index"
    template_name = "group/index.html"

    def populate(self):
        # Get groups for current user
        groups = Group.query.filter_by(client_id=g.user.client_id).all()
        return {
            "groups": sorted([transform_group(g) for g in groups],
                             key=lambda x: x["name"])
        }

    def handle_post(self, values):
        if values["group_type"] == "arn":
            if not g.user.client.is_admin:
                return response("Expected client to be admin for ARN", 403)
            thinggroup = ThingGroup(values["name_or_arn"], "")
            thinggroup.sync()
            group = Group(arn=thinggroup.arn,
                          client_id=g.user.client_id,
                          name=thinggroup.name)
            for thing in thinggroup.things:
                device = Device.query.filter_by(arn=thing.arn).first()
                if device is not None:
                    group.devices.append(device)
        else:
            new_uuid = uuid.uuid4()
            thinggroup = ThingGroup("", new_uuid.hex)
            thinggroup.sync(create=True)
            group = Group(arn=thinggroup.arn,
                          client_id=g.user.client_id,
                          name=values["name_or_arn"])
        db.session.add(group)
        db.session.commit()
        return response("Group successfully created: %s" % group.name,
                        payload={"group": transform_group(group)})


blueprint.add_url_rule("/", view_func=Index.as_view("index"))


class Manage(AppRouteView):
    route = "group.manage"
    template_name = "group/manage.html"

    def populate(self, arn):
        query = [Group.arn.endswith(arn), Group.client_id == g.user.client_id]
        group = Group.query.filter(*query).first()
        devices = Device.query.filter_by(client_id=g.user.client_id).all()
        devices_list = {}
        for device in devices:
            if devices_list.get(device.arn) is None:
                devices_list[device.arn] = (device, False)
            for group in device.groups:
                is_in_group = group.arn[-len(arn):] == arn
                devices_list[device.arn] = (device, is_in_group)
                if is_in_group:
                    break
        # transform to JSON-able output
        all_devices = [({"name": d[0].name, "arn": d[0].arn}, d[1])
                       for d in devices_list.values()]
        return {
            "group": {
                "name": group.name,
                "arn": group.arn,
                "devices": sorted([d[0] for d in all_devices if d[1]],
                                  key=lambda x: x["name"].lower())
            },
            "devices": sorted(all_devices, key=lambda x: x[0]["name"].lower()),
            "arn": arn
        }

    def handle_post(self, values, arn):
        self.redirect_args = {"arn": arn}
        query = [Group.arn.endswith(arn), Group.client_id == g.user.client_id]
        group = Group.query.filter(*query).first()
        devices = Device.query.filter_by(client_id=g.user.client_id)
        group_devices = devices.filter(Device.groups.any(
            Group.arn.endswith(arn))).all()
        for device in group_devices:  # locals are gone, remove remote
            name = "dev_" + device.name
            if values.get(name, request.form.get(name)) is None:
                # remove from remote, not in JSON or form
                group.devices.remove(device)
        for device in devices:  # locals exist, add to remote
            name = "dev_" + device.name
            if (values.get(name, request.form.get(name)) is not None and
                    device not in group.devices):
                group.devices.append(device)
        db.session.commit()
        return response("Successfully updated devices for group")


blueprint.add_url_rule("/manage/<arn>", view_func=Manage.as_view("manage"))
