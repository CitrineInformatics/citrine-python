from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop
from setuptools.command.build_py import build_py
import sys
from os.path import join
from os import walk

STRIP_DIRS = ["src", "tests"]


def strip_file(file_path):
    from strip_hints import strip_file_to_string

    if file_path.endswith('.py'):
        stripped = strip_file_to_string(file_path, to_empty=True, only_assigns_and_defs=True)
        print(file_path)
        with open(file_path, 'w') as file_obj:
            file_obj.write(stripped)


def strip_all_hints(dirnames):
    print('stripping type annotations from: {}'.format(dirnames))
    for dirname in dirnames:
        for root, dirs, files in walk(dirname):
            for file_name in files:
                strip_file(join(root, file_name))


class PostInstallCommand(install):
    """Post-installation for installation mode"""
    def run(self):
        """Python version is constrained to [3.5, 4.0), so if the minor version is < 6,
        run the script to strip type hints"""
        if sys.version_info.minor < 6:
            strip_all_hints(STRIP_DIRS)
        install.run(self)


class PostDevelopCommand(develop):
    """Post-installation for develop mode"""
    def run(self):
        """Python version is constrained to [3.5, 4.0), so if the minor version is < 6,
        run the script to strip type hints"""
        if sys.version_info.minor < 6:
            strip_all_hints(STRIP_DIRS)
        develop.run(self)


class PreBuildCommand(build_py):
    """Pre-build command for build_py"""
    def run(self):
        """Strip out all variable declaration type hints since we create a single wheel file
        for all versions of Python 3 and Python 3.5 does not support these hints"""
        strip_all_hints(STRIP_DIRS)
        build_py.run(self)


setup(name='citrine',
      version='0.35.3',
      url='http://github.com/CitrineInformatics/citrine-python',
      description='Python library for the Citrine Platform',
      author='Citrine Informatics',
      package_dir={'': 'src'},
      packages=find_packages(where='src'),
      install_requires=[
          "requests>=2.22.0,<3",
          "pyjwt>=1.7.1,<2",
          "arrow>=0.15.4,<0.16",
          "strip-hints>=0.1.8,<0.2",
          "gemd>=0.8,<0.9",
          "boto3>=1.9.226,<2",
          "botocore>=1.12.226,<2",
          "deprecation>=2.0.7,<3",
          "urllib3>=1.25.7,<2"
      ],
      cmdclass={
          'install': PostInstallCommand,
          'develop': PostDevelopCommand,
          'build_py': PreBuildCommand,
      },
      classifiers=[
          'Programming Language :: Python :: 3',
          'Programming Language :: Python :: 3.5',
          'Programming Language :: Python :: 3.6',
          'Programming Language :: Python :: 3.7',
          'Programming Language :: Python :: 3.8',
      ],
)
