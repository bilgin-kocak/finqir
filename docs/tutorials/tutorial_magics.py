# This file is derived from Qiskit Finance for use in FinQIR.
#
# (C) Copyright IBM 2017, 2024
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.
# pylint: disable=unused-argument

"""A module for version and copyright magics."""

import platform
import time
from sys import modules

from IPython import get_ipython
from IPython.core.magic import line_magic, Magics, magics_class
from IPython.display import HTML, display

import qiskit
import finqir


@magics_class
class Copyright(Magics):
    """A class of status magic functions."""

    @line_magic
    def finqir_copyright(self, line="", cell=None):
        """Display the FinQIR project and licensing notice."""
        html = "<div style='width: 100%; background-color:#d5d9e0;"
        html += "padding-left: 10px; padding-bottom: 10px; padding-right: 10px; padding-top: 5px'>"
        html += "<h3>FinQIR: independent software built on Qiskit</h3>"
        html += "<p>FinQIR includes code derived from Qiskit Finance; "
        html += "existing copyright notices are retained.</p>"
        html += "<p>This code is licensed under the Apache License, Version 2.0. You may<br>"
        html += "obtain a copy of this license in the LICENSE.txt file in the root directory<br> "
        html += "of this source tree or at http://www.apache.org/licenses/LICENSE-2.0."

        html += "<p>Any modifications or derivative works of this code must retain this<br>"
        html += "copyright notice, and modified files need to carry a notice indicating<br>"
        html += "that they have been altered from the originals.</p>"
        html += "</div>"
        return display(HTML(html))


@magics_class
class VersionTable(Magics):
    """A class of status magic functions."""

    @line_magic
    def finqir_version_table(self, line="", cell=None):
        """
        Print an HTML-formatted table with version numbers for Qiskit and its
        dependencies. This should make it possible to reproduce the environment
        and the calculation later on.
        """
        html = "<h3>Version Information</h3>"
        html += "<table>"
        html += "<tr><th>Software</th><th>Version</th></tr>"

        packages = {"finqir": finqir.__version__, "qiskit": qiskit.__version__}
        qiskit_modules = {module.split(".")[0] for module in modules.keys() if "qiskit" in module}

        for qiskit_module in qiskit_modules:
            packages[qiskit_module] = getattr(modules[qiskit_module], "__version__", None)

        for name, version in packages.items():
            if version:
                html += f"<tr><td><code>{name}</code></td><td>{version}</td></tr>"

        html += "<tr><th colspan='2'>System information</th></tr>"

        sys_info = [
            ("Python version", platform.python_version()),
            ("OS", "%s" % platform.system()),
        ]

        for name, version in sys_info:
            html += f"<tr><td>{name}</td><td>{version}</td></tr>"

        html += "<tr><td colspan='2'>%s</td></tr>" % time.strftime("%a %b %d %H:%M:%S %Y %Z")
        html += "</table>"

        return display(HTML(html))


_IP = get_ipython()
if _IP is not None:
    _IP.register_magics(VersionTable)
    _IP.register_magics(Copyright)
