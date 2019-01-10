import uuid
import io
import zipfile

import gigaspoon as gs

from flask import (Blueprint, g)
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
        else:
            super().get(arn, *args, **kwargs)

    def populate(self, arn):
        thing = Thing("", arn).sync()
        cert, (pubkey, privkey), endpoint = thing.gen_credentials()