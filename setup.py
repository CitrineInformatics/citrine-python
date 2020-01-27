from setuptools import setup, find_packages
from setuptools.command.install import install
from setuptools.command.develop import develop
import sys
import subprocess


class PostInstallCommand(install):
    """Post-installation for installation mode"""
    def run(self):
        """Python version is constrained to [3.5, 4.0), so if the minor version is < 6,
        run the script to strip type hints"""
        if sys.version_info.minor < 6:
            subprocess.call('chmod 755 scripts/strip_hints.sh', shell=True)
            subprocess.call('./scripts/strip_hints.sh', shell=True)
        install.run(self)


class PostDevelopCommand(develop):
    """Post-installation for develop mode"""
    def run(self):
        """Python version is constrained to [3.5, 4.0), so if the minor version is < 6,
        run the script to strip type hints"""
        if sys.version_info.minor < 6:
            subprocess.call('chmod 755 scripts/strip_hints.sh', shell=True)
            subprocess.call('./scripts/strip_hints.sh', shell=True)
        develop.run(self)


setup(name='citrine',
      version='0.7.1',
      url='http://github.com/CitrineInformatics/citrine-python',
      description='Python library for the Citrine Platform',
      author='Andrew Millspaugh',
      author_email='amillspaugh@citrine.io',
      package_dir={'': 'src'},
      packages=find_packages(where='src'),
      install_requires=[
          "requests>=2.22.0,<3",
          "pyjwt>=1.7.1,<2",
          "arrow>=0.15.4,<0.16",
          "strip-hints>=0.1.5,<=0.1.7",
          "taurus-citrine>=0.4.0,<0.5",
          "boto3>=1.9.226,<2",
          "botocore>=1.12.226,<2",
          "deprecation>=2.0.7,<3"
      ],
      cmdclass={
          'install': PostInstallCommand,
          'develop': PostDevelopCommand
      }
)
