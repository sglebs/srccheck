from paver.setuputils import setup
from setuptools import find_packages

setup(
    name='srccheck',
    description='Source code KALOI (using Understand).',
    packages=find_packages(),
    version='0.0.1',
    install_requires=[
        'docopt==0.6.2',
        'requests==2.10.0',
    ],
    entry_points={
        'console_scripts': [
            'srccheck = srccheck.srccheck:main',
        ],
    }
)
