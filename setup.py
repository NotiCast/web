# pylint: disable=missing-docstring
from distutils.core import setup

setup(
    name='noticast_web',
    version='0.1-dev',
    packages=['noticast_web'],
    package_data={
        "noticast_web": ["templates/*", "static/*"]
    },
    install_requires=['flask', 'flask_sqlalchemy', 'spudbucket',
                      'boto3', 'psycopg2-binary', 'pymysql'])
