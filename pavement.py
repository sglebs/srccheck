from paver.setuputils import setup
from setuptools import find_packages

setup(
    name='srccheck',
    description='Source code KALOI (using Understand).',
    packages=find_packages(),
    version='0.0.8',
    install_requires=[
        'docopt==0.6.2',
        'requests==2.10.0',
        'matplotlib==1.5.3',
        'Jinja2==2.8',
        'mpld3==0.3'
    ],
    entry_points={
        'console_scripts': [
            'srccheck = utilities.srccheck:main',
            'srchistplot = utilities.srchistplot:main',
            'srcscatterplot = utilities.srcscatterplot:main',
            'srcinstplot = utilities.srcinstplot:main',
        ],
    }
)
