# This file is part of starcraft.
#
# Copyright 2023 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License version 3, as published
# by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
# SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Craft Application Package.

This package should provide everything needed to comply with what a Craft Application
is to provide at its base.
"""

from .app import Application
from .metadata import MetadataModel
from .parts import PartsLifecycle
from .project import Project

__all__ = ["Application", "PartsLifecycle", "Project", "MetadataModel"]
