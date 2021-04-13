#!/usr/bin/env python3

# This file is managed by 'repo_helper'. Don't edit it directly.

# stdlib
import os
import re

# 3rd party
from sphinx_pyproject import SphinxConfig

config = SphinxConfig()

github_username = "sphinx-toolbox"
github_repository = "sphinx-toolbox"
author = "Dominic Davis-Foster"
project = "sphinx-toolbox"
copyright = "2020-2021 Dominic Davis-Foster"
language = "en"
package_root = "sphinx_toolbox"
extensions = [
		"sphinx_toolbox",
		"sphinx_toolbox.more_autodoc",
		"sphinx_toolbox.more_autosummary",
		"sphinx_toolbox.documentation_summary",
		"sphinx_toolbox.tweaks.param_dash",
		"sphinx_toolbox.tweaks.latex_toc",
		"sphinx.ext.intersphinx",
		"sphinx.ext.mathjax",
		"sphinxcontrib.httpdomain",
		"sphinxcontrib.extras_require",
		"sphinx.ext.todo",
		"sphinxemoji.sphinxemoji",
		"notfound.extension",
		"sphinx_copybutton",
		"sphinxcontrib.default_values",
		"sphinxcontrib.toctree_plus",
		"sphinx_debuginfo",
		"seed_intersphinx_mapping",
		"sphinx_removed_in",
		"sphinx_toolbox.pre_commit",
		"sphinx_toolbox.flake8",
		"sphinx_autofixture",
		]
sphinxemoji_style = "twemoji"
gitstamp_fmt = "%d %b %Y"
templates_path = ["_templates"]
html_static_path = ["_static"]
source_suffix = ".rst"
master_doc = "index"
suppress_warnings = ["image.nonlocal_uri"]
pygments_style = "default"
html_theme = "domdf_sphinx_theme"
html_theme_path = ["../.."]
html_show_sourcelink = True
toctree_plus_types = [
		"class",
		"confval",
		"data",
		"directive",
		"enum",
		"exception",
		"flag",
		"function",
		"method",
		"namedtuple",
		"protocol",
		"role",
		"typeddict",
		]
add_module_names = False
hide_none_rtype = True
all_typevars = True
overloads_location = "bottom"
documentation_summary = "Box of handy tools for Sphinx 🧰 📔"
autodoc_exclude_members = [
		"__dict__",
		"__class__",
		"__dir__",
		"__weakref__",
		"__module__",
		"__annotations__",
		"__orig_bases__",
		"__parameters__",
		"__subclasshook__",
		"__init_subclass__",
		"__attrs_attrs__",
		"__init__",
		"__new__",
		"__getnewargs__",
		"__abstractmethods__",
		"__hash__",
		]

github_url = f"https://github.com/{github_username}/{github_repository}"

rst_prolog = f""".. |pkgname| replace:: sphinx-toolbox
.. |pkgname2| replace:: ``sphinx-toolbox``
.. |browse_github| replace:: `Browse the GitHub Repository <{github_url}>`__
"""

slug = re.sub(r'\W+', '-', project.lower())
release = version = config.version

todo_include_todos = bool(os.environ.get("SHOW_TODOS", 0))

intersphinx_mapping = {
		"python": ("https://docs.python.org/3/", None),
		"sphinx": ("https://www.sphinx-doc.org/en/stable/", None),
		"pytest": ("https://docs.pytest.org/en/stable", None),
		"pytest-regressions": ("https://pytest-regressions.readthedocs.io/en/latest/", None),
		}

html_theme_options = {"logo_only": False}

html_context = {
		"display_github": True,
		"github_user": "sphinx-toolbox",
		"github_repo": "sphinx-toolbox",
		"github_version": "master",
		"conf_py_path": "/doc-source/",
		}
htmlhelp_basename = slug

latex_documents = [("index", f'{slug}.tex', project, author, "manual")]
man_pages = [("index", slug, project, [author], 1)]
texinfo_documents = [("index", slug, project, author, slug, project, "Miscellaneous")]

toctree_plus_types = set(toctree_plus_types)

autodoc_default_options = {
		"members": None,  # Include all members (methods).
		"special-members": None,
		"autosummary": None,
		"show-inheritance": None,
		"exclude-members": ','.join(autodoc_exclude_members),
		}

html_logo = "../sphinx_toolbox.png"
toctree_plus_types.add("fixture")
__import__("sys").path.append(os.path.abspath(".."))
