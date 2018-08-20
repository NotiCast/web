import uuid

import gigaspoon as gs

from flask import (Blueprint, g)
from .auth import login_required, admin_required
from .iot_util import get_things, Thing
from .models import Device, db
from .app_view import AppRouteView, response

blueprint = Blueprint("device", __name__, url_prefix="/device")


class NewCert(AppRouteView):
    decorators = [login_required]
    template_name = "device/new_credentials.html"

    def populate(self, arn):
        thing = Thing("", arn).sync()
        cert, (pubkey, privkey), endpoint = thing.gen_credentials()
        return {
            "cert": cert,
            "pubkey": pubkey,
            "privkey": privkey,
            "endpoint": endpoint["endpointAddress"],
            "arn": thing.arn
        }


blueprint.add_url_rule("/new_cert/<arn>",
                       view_func=NewCert.as_view("new_cert"))


class Register(AppRouteView):
    decorators = [login_required,
                  gs.validator(gs.v.LengthValidator("device_name", min=8))]
    redirect_to = "index"
    template_name = "device/register.html"

    def handle_post(self, values):
        name = values["device_name"]
        thing = Thing("", uuid.uuid4().hex)
        thing.sync(create=True)
        device = Device(arn=thing.arn,
                        client_id=g.user.client_id,
                        name=name)
        db.session.add(device)
        db.session.commit()

        return response("Device successfully created: %s" % name,
                        payload={"name": name, "arn": thing.arn})


blueprint.add_url_rule("/register", view_func=Register.as_view("register"))


class FromArn(AppRouteView):
    decorators = [admin_required,
                  gs.validator(gs.v.ExistsValidator("device_arn"))]
    route = "device.from_arn"
    template_name = "device/from_arn.html"

    def handle_post(self, values):
        arn = values["device_arn"]
        for thing in (thing for thing in get_things() if thing.arn == arn):
            thing.sync()
            device = Device(arn=arn,
                            client_id=g.user.client_id,
                            name=thing.name)
            db.session.add(device)
            db.session.commit()
            self.redirect_to = "index"
            return response("Device successfully created: %s" % thing.name,
                            payload={"name": thing.name, "arn": thing.arn})
        else:
            return response("Device was not found", status_code=404)


blueprint.add_url_rule("/from_arn", view_func=FromArn.as_view("from_arn"))
