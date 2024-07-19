# -- Path setup --------------------------------------------------------------

import os
import sys
sys.path.insert(0, os.path.relpath('library'))


# -- Project information -----------------------------------------------------

project = 'racecar-neo-library'
copyright = '2024, MIT.'
author = 'BWSI Autonomous RACECAR'


# -- General configuration ---------------------------------------------------

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'myst_parser'
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

pygments_style = 'default'
pygments_style_dark = 'lightbulb'

# -- Options for HTML output -------------------------------------------------

html_permalinks_icon = '<span>#</span>'
html_theme = 'sphinxawesome_theme'
html_static_path = ['_static']
