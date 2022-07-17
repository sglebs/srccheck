from paver.setuputils import setup
from setuptools import find_packages
from utilities import VERSION
setup(
    name='srccheck',
    description='Source code KALOI (using Understand).',
    packages=find_packages(),
    version=VERSION,
    url='https://github.com/sglebs/srccheck',
    author='Marcio Marchini',
    author_email='marcio@betterdeveloper.net',
    install_requires=[
        'docopt>=0.6.2',
        'requests>=2.10.0',
        'numpy==1.18',  # required version for proper matplotlib compilation in Python 3.8, 3.9, 3.10
        'matplotlib==2.2.4',
        'Jinja2==2.8',
        'mpld3==0.5.1'
    ],
    entry_points={
        'console_scripts': [
            'srccheck = utilities.srccheck:main',
            'srchistplot = utilities.srchistplot:main',
            'srcscatterplot = utilities.srcscatterplot:main',
            'srcinstplot = utilities.srcinstplot:main',
            'csvhistplot = utilities.csvhistplot:main',
            'srcdiffplot = utilities.srcdiffplot:main',
            'csvkaloi = utilities.csvkaloi:main',
            'csvscatterplot = utilities.csvscatterplot:main',
            'xmlkaloi = utilities.xmlkaloi:main',
            'jd2csv = utilities.jd2csv:main',
        ],
    }
)
