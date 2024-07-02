# -- Path setup --------------------------------------------------------------

import os
import sys
sys.path.insert(0, os.path.relpath('library'))


# -- Project information -----------------------------------------------------

project = 'racecar-neo-library'
copyright = '2024, BWSI Autonomous RACECAR'
author = 'BWSI Autonomous RACECAR'


# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon'
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

html_theme = 'alabaster'
html_static_path = ['_static']
