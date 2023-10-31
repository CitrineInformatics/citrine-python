from setuptools import setup, find_packages
from os import path

# read the contents of your README file
this_directory = path.abspath(path.dirname(__file__))
with open(path.join(this_directory, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

about = {}
with open(path.join(this_directory, 'src', 'citrine', '__version__.py'), 'r') as f:
    exec(f.read(), about)

setup(name='citrine',
      # Update this in src/citrine/__version__.py
      version=about['__version__'],
      python_requires='>=3.7',
      url='http://github.com/CitrineInformatics/citrine-python',
      description='Python library for the Citrine Platform',
      long_description=long_description,
      long_description_content_type='text/markdown',
      author='Citrine Informatics',
      package_dir={'': 'src'},
      packages=find_packages(where='src'),
      install_requires=[
          "requests>=2.31.0,<3",
          "pyjwt>=2,<3",
          "arrow>=0.15.4,<2",
          "gemd>=1.15.0,<2",
          "boto3>=1.17.93,<2",
          "botocore>=1.20.95,<2",
          "deprecation>=2.1.0,<3",
          "urllib3>=1.26.18,<3",
          "tqdm>=4.62.3,<5"
      ],
      extras_require={
          "builders": [
              "pandas>=1.3.5,<3"
          ],
          "../tests": [
              "factory-boy>=2.12.0,<4",
              "mock>=3.0.5,<5",
              "pandas>=1.3.5,<3",
              "pytest>=6.2.5,<8",
              "pytz>=2020.1",
              "requests-mock>=1.7.0,<2",
          ]
      },
      classifiers=[
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
      ],
      )
