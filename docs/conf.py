import os
import sys
from datetime import date

sys.path.insert(0, os.path.abspath("../"))

project = "pysolarmanv5"
copyright = f"{date.today().year}, Jonathan McCrohan"
author = "Jonathan McCrohan <jmccrohan@gmail.com>"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.viewcode",
    "sphinx.ext.todo",
    "myst_parser",
    "sphinxcontrib.packetdiag",
]

html_theme = "furo"

html_theme_options = {
    "source_repository": "https://github.com/jmccrohan/pysolarmanv5/",
    "source_branch": "main",
    "source_directory": "docs/",
}

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    #'private-members': True,
}

autodoc_mock_imports = ["umodbus"]

autosectionlabel_prefix_document = True

packetdiag_html_image_format = "SVG"

html_static_path = ["_static"]

html_css_files = [
    "css/custom.css",
]

# todo_include_todos = True
