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
      python_requires='>=3.8',
      url='http://github.com/CitrineInformatics/citrine-python',
      description='Python library for the Citrine Platform',
      long_description=long_description,
      long_description_content_type='text/markdown',
      author='Citrine Informatics',
      package_dir={'': 'src'},
      packages=find_packages(where='src'),
      install_requires=[
          "requests>=2.32.2,<3",
          "pyjwt>=2,<3",
          "arrow>=1.0.0,<2",
          "gemd>=2.1.9,<3",
          "boto3>=1.34.35,<2",
          "deprecation>=2.1.0,<3",
          "urllib3>=1.26.18,<3",
          "tqdm>=4.27.0,<5",
      ],
      extras_require={
          "tests": [
              "factory-boy>=3.3.0,<4",
              "mock>=5.1.0,<6",
              "pandas>=2.0.3,<3",
              "pytest>=8.0.0,<9",
              "requests-mock>=1.11.0,<2",
          ]
      },
      classifiers=[
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.8',
          'Programming Language :: Python :: 3.9',
          'Programming Language :: Python :: 3.10',
          'Programming Language :: Python :: 3.11',
      ],
      )
