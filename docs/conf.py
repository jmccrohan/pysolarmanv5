import os
import sys
from datetime import date

sys.path.insert(0, os.path.abspath('../pysolarmanv5'))

project = 'pysolarmanv5'
copyright = f"{date.today().year}, Jonathan McCrohan"
author = 'Jonathan McCrohan <jmccrohan@gmail.com>'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.autosectionlabel',
    'sphinx.ext.viewcode',
    'sphinx.ext.todo',
    'myst_parser',
    'sphinxcontrib.packetdiag',
    ]

html_theme = 'furo'

html_theme_options = {
    "source_repository": "https://github.com/jmccrohan/pysolarmanv5/",
    "source_branch": "main",
    "source_directory": "docs/",
}

autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    #'private-members': True,
    }

autodoc_mock_imports = ["umodbus"]

packetdiag_html_image_format = 'SVG'

#todo_include_todos = True
