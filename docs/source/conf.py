# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import citrine
import os
import sys
sys.path.insert(0, os.path.abspath('../../src'))


# -- Project information -----------------------------------------------------

project = 'Citrine Python'
copyright = '2019, Citrine Informatics'
author = 'Citrine Informatics'

# The short X.Y version.
version = citrine.__version__
# The full version, including alpha/beta/rc tags.
release = citrine.__version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinxcontrib.apidoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.intersphinx',
    'sphinx_rtd_theme'
]

# Use the sphinxcontrib.apidoc extension to wire in the sphinx-apidoc invocation
# to the build process, eliminating the need for an extra call during the
# build.
#
# See: https://github.com/sphinx-contrib/apidoc
apidoc_module_dir = '../../src'
apidoc_output_dir = 'reference'
apidoc_excluded_paths = ['tests']
apidoc_separate_modules = True

# Use intersphinx to link to classes in Sphinx docs for other libraries
# See: https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html
intersphinx_mapping = {'gemd-python': ('https://citrineinformatics.github.io/gemd-python/', None)}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "sphinx_rtd_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

autodoc_member_order = 'groupwise'
autodoc_mock_imports = []  # autodoc_mock_imports allows Spyinx to ignore any external modules listed in the array

html_favicon = '_static/favicon.png'
html_logo = '_static/logo.png'
html_theme_options = {
    'sticky_navigation': False,
    'logo_only': True
}
