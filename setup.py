from os import path
from setuptools import find_packages, setup


with open('requirements.txt') as rq:
    requirements = rq.read().splitlines()

install_requires = []
dependency_links = []
EGG_MARK = '#egg='
for line in requirements:
    if line.startswith('-e git:') or line.startswith('-e git+') or \
            line.startswith('git:') or line.startswith('git+'):
        if EGG_MARK in line:
            package_name = line[line.find(EGG_MARK) + len(EGG_MARK):]
            install_requires.append(package_name)
            dependency_links.append(line)
        else:
            print('Dependency to a git repository should have the format:')
            print('git+ssh://git@github.com/xxxxx/xxxxxx#egg=package_name')
    else:
        install_requires.append(line)

setup(
    name='beacon-presence',
    version='0.0.1',
    description='Presence detection using BLE beacons',
    author='Sören Oldag',
    author_email='soeren_oldag@freenet.de',
    license='MIT',
    url='https://github.com/soldag/beacon-presence',
    packages=find_packages(),
    install_requires=install_requires,
    dependency_links=dependency_links,
    entry_points={
        'console_scripts': [
              'beacon-presence = beacon_presence.__main__:main'
          ]
    },
)