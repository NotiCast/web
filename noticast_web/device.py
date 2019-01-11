import uuid
import io
import zipfile

import gigaspoon as gs

from flask import (Blueprint, g, request, send_file)
from .auth import login_required, admin_required
from .iot_util import get_things, Thing
from .models import Device, db
from .app_view import AppRouteView, response

blueprint = Blueprint("device", __name__, url_prefix="/device")


def generate_zip_file_from_dict(input):
    output_file = io.BytesIO()
    zf = zipfile.ZipFile(output_file, "w")

    for filename, content in ((x, input[x]) for x in input):
        with zf.open(filename, "w") as f:
            f.write(content)

    zf.close()
    output_file.seek(0)
    return output_file


class NewCert(AppRouteView):
    decorators = [login_required]
    template_name = "device/new_credentials.html"

    def get(self, arn, *args, **kwargs):
        format = request.args.get("format")
        if format is not None:
            print("format:", format)
            # Custom format supplied in GET parameters
            if format == "zip":
                values = self.populate(arn)
                f = generate_zip_file_from_dict({
                    "cert.crt": values["cert"],
                    "key": values["privkey"],
                    "iot-endpoint": values["endpoint"],
                    "device-arn": values["arn"]
                })
                return send_file(f, mimetype="application/zip",
                                 as_attachment=True,
                                 attachment_name="credentials.zip")
        return super().get(arn, *args, **kwargs)

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
                  gs.validator(gs.v.Length("device_name", min=8))]
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
                  gs.validator(gs.v.Exists("device_arn"))]
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
