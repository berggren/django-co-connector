import os
from setuptools import setup, find_packages
import django_co_connector


def read(fname):
    try:
        return open(os.path.join(os.path.dirname(__file__), fname)).read()
    except IOError:
        return ''


setup(
    name="django_co_connector",
    version=django_co_connector.__version__,
    description=read('DESCRIPTION'),
    long_description=read('README.rst'),
    keywords='co gmp groups',
    packages=find_packages(),
    author='',
    author_email='',
    url="",
    include_package_data=True,
    test_suite='django_co_connector.tests.runtests.runtests',
)
