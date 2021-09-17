#!/usr/bin/env python3
#
#  autonamedtuple.py
r"""
A Sphinx directive for documenting :class:`NamedTuples <typing.NamedTuple>` in Python.

.. versionadded:: 0.8.0
.. extensions:: sphinx_toolbox.more_autodoc.autonamedtuple
.. versionchanged:: 1.5.0

	``__new__`` methods are documented regardless of other exclusion settings
	if the annotations differ from the namedtuple itself.


Usage
---------

.. rst:directive:: autonamedtuple

	Directive to automatically document a :class:`typing.NamedTuple` or :func:`collections.namedtuple`.

	The output is based on the :rst:dir:`autoclass` directive.
	The list of parameters and the attributes are replaced by a list of Fields,
	combining the types and docstrings from the class docstring individual attributes.
	These will always be shown regardless of the state of the ``:members:`` option.

	Otherwise the directive behaves the same as :rst:dir:`autoclass`, and takes all of its arguments.
	See https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html for further information.

	.. versionadded:: 0.8.0


.. rst:role:: namedtuple

	Role which provides a cross-reference to the documentation generated by :rst:dir:`autonamedtuple`.


.. seealso:: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html


:bold-title:`Examples`

.. literalinclude:: ../../../autonamedtuple_demo.py
	:language: python
	:tab-width: 4
	:linenos:
	:lines: 1-59

.. rest-example::

	.. automodule:: autonamedtuple_demo
		:no-autosummary:
		:exclude-members: Movie

	.. autonamedtuple:: autonamedtuple_demo.Movie

	This function takes a single argument, the :namedtuple:`~.Movie` to watch.


API Reference
---------------

"""
#
#  Copyright © 2020-2021 Dominic Davis-Foster <dominic@davis-foster.co.uk>
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy
#  of this software and associated documentation files (the "Software"), to deal
#  in the Software without restriction, including without limitation the rights
#  to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#  copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in all
#  copies or substantial portions of the Software.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
#  EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
#  MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#  IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#  DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#  OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE
#  OR OTHER DEALINGS IN THE SOFTWARE.
#
#  Parts based on https://github.com/sphinx-doc/sphinx
#  |  Copyright (c) 2007-2020 by the Sphinx team (see AUTHORS file).
#  |  BSD Licensed
#  |  All rights reserved.
#  |
#  |  Redistribution and use in source and binary forms, with or without
#  |  modification, are permitted provided that the following conditions are
#  |  met:
#  |
#  |  * Redistributions of source code must retain the above copyright
#  |   notice, this list of conditions and the following disclaimer.
#  |
#  |  * Redistributions in binary form must reproduce the above copyright
#  |   notice, this list of conditions and the following disclaimer in the
#  |   documentation and/or other materials provided with the distribution.
#  |
#  |  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
#  |  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
#  |  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
#  |  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
#  |  HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
#  |  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
#  |  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
#  |  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
#  |  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  |  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
#  |  OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

# stdlib
import inspect
import re
import sys
import textwrap
import warnings
from textwrap import dedent
from typing import Any, Dict, List, Tuple, Type, get_type_hints

# 3rd party
from sphinx.application import Sphinx
from sphinx.deprecation import RemovedInSphinx50Warning
from sphinx.domains import ObjType
from sphinx.domains.python import PyClasslike, PyXRefRole
from sphinx.ext.autodoc import ClassDocumenter, Documenter, Options
from sphinx.ext.autodoc.directive import DocumenterBridge
from sphinx.locale import _
from sphinx.pycode import ModuleAnalyzer

# this package
from sphinx_toolbox.more_autodoc import ObjectMembers
from sphinx_toolbox.more_autodoc.typehints import format_annotation
from sphinx_toolbox.utils import (
		Param,
		SphinxExtMetadata,
		add_nbsp_substitution,
		allow_subclass_add,
		baseclass_is_private,
		is_namedtuple,
		metadata_add_version,
		parse_parameters
		)

__all__ = ["NamedTupleDocumenter", "setup"]

field_alias_re = re.compile("Alias for field number [0-9]+")


class NamedTupleDocumenter(ClassDocumenter):
	r"""
	Sphinx autodoc :class:`~sphinx.ext.autodoc.Documenter`
	for documenting :class:`typing.NamedTuple`\s.

	.. versionadded:: 0.8.0

	.. versionchanged:: 0.1.0

		Will no longer attempt to find attribute docstrings from other namedtuple classes.
	"""  # noqa: D400

	objtype = "namedtuple"
	directivetype = "namedtuple"
	priority = 20
	object: Type  # noqa: A003  # pylint: disable=redefined-builtin

	def __init__(self, directive: DocumenterBridge, name: str, indent: str = '') -> None:
		super().__init__(directive, name, indent)
		self.options = Options(self.options.copy())

	@classmethod
	def can_document_member(
			cls,
			member: Any,
			membername: str,
			isattr: bool,
			parent: Any,
			) -> bool:
		"""
		Called to see if a member can be documented by this documenter.

		:param member: The member being checked.
		:param membername: The name of the member.
		:param isattr:
		:param parent: The parent of the member.
		"""

		return is_namedtuple(member)

	def add_content(self, more_content: Any, no_docstring: bool = True):
		r"""
		Add extra content (from docstrings, attribute docs etc.),
		but not the :class:`typing.NamedTuple`\'s docstring.

		:param more_content:
		:param no_docstring:
		"""  # noqa: D400

		with warnings.catch_warnings():
			# TODO: work out what to do about this
			warnings.simplefilter("ignore", RemovedInSphinx50Warning)

			Documenter.add_content(self, more_content, True)

		# set sourcename and add content from attribute documentation
		sourcename = self.get_sourcename()

		params, pre_output, post_output = self._get_docstring()

		for line in pre_output:
			self.add_line(line, sourcename)

	def _get_docstring(self) -> Tuple[Dict[str, Param], List[str], List[str]]:
		"""
		Returns params, pre_output, post_output.
		"""

		# Size varies depending on docutils config
		tab_size = self.env.app.config.docutils_tab_width

		if self.object.__doc__:
			docstring = dedent(self.object.__doc__).expandtabs(tab_size).split('\n')
		elif "show-inheritance" not in self.options:
			docstring = [":class:`typing.NamedTuple`."]
		else:
			docstring = ['']

		docstring = list(self.process_doc([docstring]))

		return parse_parameters(docstring, tab_size=tab_size)

	def add_directive_header(self, sig: str) -> None:
		"""
		Add the directive's header, and the inheritance information if the ``:show-inheritance:`` flag set.

		:param sig: The NamedTuple's signature.
		"""

		super().add_directive_header(sig)

		if "show-inheritance" not in self.options:
			return

		acceptable_bases = {
				"   Bases: :class:`tuple`",
				"   Bases: :class:`tuple`, :class:`typing.Generic`",
				"   Bases: :class:`NamedTuple`",
				}

		if self.directive.result[-1] in acceptable_bases or baseclass_is_private(self.object):
			# TODO: multiple inheritance

			if getattr(self.env.config, "generic_bases_fully_qualified", False):
				# Might not be present; extension might not be enabled
				prefix = ''
			else:
				prefix = '~'

			if hasattr(self.object, "__annotations__"):
				self.directive.result[-1] = f"   Bases: :class:`{prefix}typing.NamedTuple`"
			else:
				self.directive.result[-1] = f"   Bases: :func:`{prefix}collections.namedtuple`"

	def filter_members(
			self,
			members: ObjectMembers,
			want_all: bool,
			) -> List[Tuple[str, Any, bool]]:
		"""
		Filter the list of members to always include ``__new__`` if it has a different signature to the tuple.

		:param members:
		:param want_all:
		"""

		all_hints = get_type_hints(self.object)
		class_hints = {k: all_hints[k] for k in self.object._fields if k in all_hints}

		# TODO: need a better way to partially resolve type hints, and warn about failures
		new_hints = get_type_hints(
				self.object.__new__,
				globalns=sys.modules[self.object.__module__].__dict__,
				localns=self.object.__dict__,
				)

		# Stock NamedTuples don't have these, but customised collections.namedtuple or hand-rolled classes may
		if "cls" in new_hints:
			new_hints.pop("cls")
		if "return" in new_hints:
			new_hints.pop("return")

		if class_hints and new_hints and class_hints != new_hints:
			#: __new__ has a different signature or different annotations

			def unskip_new(app, what, name, obj, skip, options):
				if name == "__new__":
					return False
				return None

			listener_id = self.env.app.connect("autodoc-skip-member", unskip_new)
			members_ = super().filter_members(members, want_all)
			self.env.app.disconnect(listener_id)
			return members_

		else:
			return super().filter_members(members, want_all)

	def sort_members(
			self,
			documenters: List[Tuple[Documenter, bool]],
			order: str,
			) -> List[Tuple[Documenter, bool]]:
		r"""
		Sort the :class:`typing.NamedTuple`\'s members.

		:param documenters:
		:param order:
		"""

		# The documenters for the fields and methods, in the desired order
		# The fields will be in bysource order regardless of the order option
		documenters = super().sort_members(documenters, order)

		# Size varies depending on docutils config
		a_tab = ' ' * self.env.app.config.docutils_tab_width

		# Mapping of member names to docstrings (as list of strings)
		member_docstrings: Dict[str, List[str]]

		try:
			namedtuple_source = textwrap.dedent(inspect.getsource(self.object))

			# Mapping of member names to docstrings (as list of strings)
			member_docstrings = {
					k[1]: v
					for k,
					v in ModuleAnalyzer.for_string(namedtuple_source, self.object.__module__
													).find_attr_docs().items()
					}

		except (TypeError, OSError):
			member_docstrings = {}

		# set sourcename and add content from attribute documentation
		sourcename = self.get_sourcename()

		params, pre_output, post_output = self._get_docstring()

		self.add_line('', sourcename)

		self.add_line(":Fields:", sourcename)
		# TODO: Add xref targets for each field as an attribute
		# TODO: support for default_values
		self.add_line('', sourcename)

		fields = self.object._fields

		for pos, field in enumerate(fields):
			doc: List[str] = ['']
			arg_type: str = ''

			# Prefer doc from class docstring
			if field in params:
				doc, arg_type = params.pop(field).values()  # type: ignore

			# Otherwise use attribute docstring
			if not ''.join(doc).strip() and field in member_docstrings:
				doc = member_docstrings[field]

			# Fallback to namedtuple's default docstring
			if not ''.join(doc).strip():
				doc = [getattr(self.object, field).__doc__]

			# Prefer annotations over docstring types
			type_hints = get_type_hints(self.object)
			if type_hints:
				if field in type_hints:
					arg_type = format_annotation(type_hints[field])

			field_entry = [f"{a_tab}{pos})", "|nbsp|", f"**{field}**"]
			if arg_type:
				field_entry.append(f"({arg_type}\\)")
			field_entry.append("--")
			field_entry.extend(doc)

			if field_alias_re.match(getattr(self.object, field).__doc__ or ''):
				getattr(self.object, field).__doc__ = ' '.join(doc)

			self.add_line(' '.join(field_entry), sourcename)

		self.add_line('', sourcename)

		for line in post_output:
			self.add_line(line, sourcename)

		self.add_line('', sourcename)

		# Remove documenters corresponding to fields and return the rest
		return [d for d in documenters if d[0].name.split('.')[-1] not in fields]


@metadata_add_version
def setup(app: Sphinx) -> SphinxExtMetadata:
	"""
	Setup :mod:`sphinx_toolbox.more_autodoc.autonamedtuple`.

	.. versionadded:: 0.8.0

	:param app: The Sphinx application.
	"""

	# Hack to get the docutils tab size, as there doesn't appear to be any other way
	app.setup_extension("sphinx_toolbox.tweaks.tabsize")

	app.registry.domains["py"].object_types["namedtuple"] = ObjType(_("namedtuple"), "namedtuple", "class", "obj")
	app.add_directive_to_domain("py", "namedtuple", PyClasslike)
	app.add_role_to_domain("py", "namedtuple", PyXRefRole())

	allow_subclass_add(app, NamedTupleDocumenter)

	add_nbsp_substitution(app.config)

	return {"parallel_read_safe": True}
