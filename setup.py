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
      url='http://github.com/CitrineInformatics/citrine-python',
      description='Python library for the Citrine Platform',
      long_description=long_description,
      long_description_content_type='text/markdown',
      author='Citrine Informatics',
      package_dir={'': 'src'},
      packages=find_packages(where='src'),
      install_requires=[
          "requests>=2.22.0,<3",
          "pyjwt>=1.7.1,<2",
          "arrow>=0.15.4,<0.16",
          "gemd>=0.18.0,<1",
          "boto3>=1.9.226,<2",
          "botocore>=1.12.226,<2",
          "deprecation>=2.0.7,<3",
          "urllib3>=1.25.7,<2"
      ],
      extras_require={
          "builders": [
              "pandas>=1.0.3,<2"
          ]
      },
      classifiers=[
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
      ],
)
