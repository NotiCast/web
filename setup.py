# pylint: disable=missing-docstring
from distutils.core import setup

setup(
    name='noticast_web',
    version='0.1-dev',
    packages=['noticast_web'],
    install_requires=['flask', 'flask-sqlalchemy'])
