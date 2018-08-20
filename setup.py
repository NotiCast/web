# pylint: disable=missing-docstring
from distutils.core import setup

import os

files = []
for directory in ["noticast_web/static", "noticast_web/templates"]:
    for path, dirs, filenames in os.walk(directory):
        files.append(os.path.join("..", path, "*"))

print(files)

setup(
    name='noticast_web',
    version='0.1-dev',
    packages=['noticast_web', 'noticast_web.rds_models'],
    package_data={
        "noticast_web": files
    },
    install_requires=['flask', 'flask_sqlalchemy', 'gigaspoon',
                      'boto3', 'psycopg2-binary', 'pymysql', 'raven[flask]'])
