from setuptools import setup

setup(
    name='app-aware-nsm',
    packages=['apis', 'core'],
    include_package_data=True,
    install_requires=['flask', 'flask-restx'])
