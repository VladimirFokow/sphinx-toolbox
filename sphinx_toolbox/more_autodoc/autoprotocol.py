#!/usr/bin/env python3
#
#  autoprotocol.py
r"""
A Sphinx directive for documenting :class:`Protocols <typing.Protocol>` in Python.

.. versionadded:: 0.2.0
.. extensions:: sphinx_toolbox.more_autodoc.autoprotocol
.. versionchanged:: 0.6.0  Moved from :mod:`sphinx_toolbox.autoprotocol`.
.. versionchanged:: 2.13.0  Added support for generic bases, such as ``class SupportsAbs(Protocol[T_co]): ...``.


Usage
-------

.. latex:vspace:: -20px

.. rst:directive:: autoprotocol

	Directive to automatically document a :class:`typing.Protocol`.

	The output is based on the :rst:dir:`autoclass` directive, but with a few differences:

	* Private members are always excluded.
	* Special members (dunder methods) are always included.
	* Undocumented members are always included.

	The following options from :rst:dir:`autoclass` are available:

	.. rst:directive:option:: noindex
		:type: flag

		Do not generate index entries for the documented object (and all autodocumented members).

	.. rst:directive:option:: member-order
		:type: string

		Override the global value of :any:`sphinx:autodoc_member_order` for one directive.

	.. rst:directive:option:: show-inheritance
		:type: flag

		Inserts a list of base classes just below the protocol's signature.


.. rst:role:: protocol

	Role which provides a cross-reference to the documentation generated by :rst:dir:`autoprotocol`.

.. latex:vspace:: 5px
.. seealso:: https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html
.. latex:clearpage::

:bold-title:`Examples:`

.. literalinclude:: ../../../autoprotocol_demo.py
	:language: python
	:tab-width: 4
	:lines: 1-31
	:linenos:

.. rest-example::

	.. automodule:: autoprotocol_demo
		:members:
		:no-autosummary:
		:exclude-members: HasGreaterThan

	.. autoprotocol:: autoprotocol_demo.HasGreaterThan

	The objects being sorted must implement the :protocol:`~.HasGreaterThan` protocol.


.. latex:vspace:: 30px


API Reference
--------------

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
import sys
from typing import Any, Callable, Dict, List, Tuple

# 3rd party
from sphinx.application import Sphinx
from sphinx.domains import ObjType
from sphinx.domains.python import PyClasslike, PyXRefRole
from sphinx.ext.autodoc import (
		INSTANCEATTR,
		ClassDocumenter,
		Documenter,
		Options,
		exclude_members_option,
		member_order_option
		)
from sphinx.ext.autodoc.directive import DocumenterBridge
from sphinx.locale import _
from sphinx.util.inspect import getdoc, safe_getattr

# this package
from sphinx_toolbox.more_autodoc import ObjectMembers
from sphinx_toolbox.more_autodoc.generic_bases import _add_generic_bases
from sphinx_toolbox.utils import (
		SphinxExtMetadata,
		add_fallback_css_class,
		allow_subclass_add,
		filter_members_warning,
		flag,
		metadata_add_version
		)

if sys.version_info < (3, 8):  # pragma: no cover (>=py38)
	# 3rd party
	from typing_extensions import _ProtocolMeta
else:  # pragma: no cover (<py38)
	# stdlib
	from typing import _ProtocolMeta

__all__ = ("ProtocolDocumenter", "setup")

runtime_message = (
		"This protocol is `runtime checkable "
		"<https://www.python.org/dev/peps/pep-0544/#runtime-checkable-decorator-and-narrowing-types-by-isinstance>`_."
		)


class ProtocolDocumenter(ClassDocumenter):
	r"""
	Sphinx autodoc :class:`~sphinx.ext.autodoc.Documenter`
	for documenting :class:`typing.Protocol`\s.
	"""  # noqa: D400

	objtype = "protocol"
	directivetype = "protocol"
	priority = 20
	option_spec: Dict[str, Callable] = {
			"noindex": flag,
			"member-order": member_order_option,
			"show-inheritance": flag,
			"exclude-protocol-members": exclude_members_option,
			}

	globally_excluded_methods = {
			"__module__",
			"__new__",
			"__init__",
			"__subclasshook__",
			"__doc__",
			"__tree_hash__",
			"__extra__",
			"__orig_bases__",
			"__origin__",
			"__parameters__",
			"__next_in_mro__",
			"__slots__",
			"__args__",
			"__dict__",
			"__weakref__",
			"__annotations__",
			"__abstractmethods__",
			"__class_getitem__",
			"__init_subclass__",
			}

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

		# _is_protocol = True
		return isinstance(member, _ProtocolMeta)

	def add_directive_header(self, sig: str) -> None:
		"""
		Add the directive header.

		:param sig:
		"""

		sourcename = self.get_sourcename()

		if self.doc_as_attr:
			self.directivetype = "attribute"

		Documenter.add_directive_header(self, sig)

		if self.analyzer and '.'.join(self.objpath) in self.analyzer.finals:
			self.add_line("   :final:", sourcename)

		# add inheritance info, if wanted
		if not self.doc_as_attr and self.options.show_inheritance:
			_add_generic_bases(self)

	def format_signature(self, **kwargs: Any) -> str:
		"""
		Protocols do not have a signature.
		"""

		return ''  # pragma: no cover

	def add_content(self, more_content: Any, no_docstring: bool = False) -> None:
		"""
		Add the autodocumenter content.

		:param more_content:
		:param no_docstring:
		"""

		super().add_content(more_content=more_content, no_docstring=no_docstring)

		sourcename = self.get_sourcename()

		if not getdoc(self.object) and "show-inheritance" not in self.options:
			self.add_line(":class:`typing.Protocol`.", sourcename)
			self.add_line('', sourcename)

		if hasattr(self.object, "_is_runtime_protocol") and self.object._is_runtime_protocol:
			self.add_line(runtime_message, sourcename)
			self.add_line('', sourcename)

		self.add_line(
				"Classes that implement this protocol must have the following methods / attributes:", sourcename
				)
		self.add_line('', sourcename)

	def document_members(self, all_members: bool = False) -> None:
		"""
		Generate reST for member documentation.

		All members are always documented.
		"""

		super().document_members(True)

	def filter_members(
			self,
			members: ObjectMembers,
			want_all: bool,
			) -> List[Tuple[str, Any, bool]]:
		"""
		Filter the given member list.

		:param members:
		:param want_all:
		"""

		ret = []

		# process members and determine which to skip
		for (membername, member) in members:
			# if isattr is True, the member is documented as an attribute

			if safe_getattr(member, "__sphinx_mock__", False):
				# mocked module or object
				keep = False  # pragma: no cover

			elif (
					self.options.get("exclude-protocol-members", [])
					and membername in self.options["exclude-protocol-members"]
					):
				# remove members given by exclude-protocol-members
				keep = False  # pragma: no cover

			elif membername.startswith('_') and not (membername.startswith("__") and membername.endswith("__")):
				keep = False

			elif membername not in self.globally_excluded_methods:
				# Magic method you wouldn't overload, or private method.
				if membername in dir(self.object.__base__):
					keep = member is not getattr(self.object.__base__, membername)
				else:
					keep = True

			else:
				keep = False

			# give the user a chance to decide whether this member
			# should be skipped
			if self.env.app:
				# let extensions preprocess docstrings
				try:  # pylint: disable=R8203
					skip_user = self.env.app.emit_firstresult(
							"autodoc-skip-member",
							self.objtype,
							membername,
							member,
							not keep,
							self.options,
							)

					if skip_user is not None:
						keep = not skip_user

				except Exception as exc:
					filter_members_warning(member, exc)
					keep = False

			if keep:
				ret.append((membername, member, member is INSTANCEATTR))

		return ret


class _PyProtocollike(PyClasslike):
	"""
	Description of a Protocol-like object.
	"""

	def get_index_text(self, modname: str, name_cls: Tuple[str, str]) -> str:
		if self.objtype == "protocol":
			return _("%s (protocol in %s)") % (name_cls[0], modname)
		else:
			return super().get_index_text(modname, name_cls)


@metadata_add_version
def setup(app: Sphinx) -> SphinxExtMetadata:
	"""
	Setup :mod:`sphinx_toolbox.more_autodoc.autoprotocol`.

	:param app: The Sphinx application.
	"""

	app.registry.domains["py"].object_types["protocol"] = ObjType(_("protocol"), "protocol", "class", "obj")
	app.add_directive_to_domain("py", "protocol", _PyProtocollike)
	app.add_role_to_domain("py", "protocol", PyXRefRole())
	app.connect("object-description-transform", add_fallback_css_class({"protocol": "class"}))

	allow_subclass_add(app, ProtocolDocumenter)

	return {"parallel_read_safe": True}
