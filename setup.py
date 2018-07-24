# pylint: disable=missing-docstring
from distutils.core import setup

setup(
    name='noticast_web',
    version='0.1-dev',
    packages=['noticast_web'],
    include_package_data=True,
    install_requires=['flask', 'flask-sqlalchemy'])
