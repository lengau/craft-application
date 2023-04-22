# This file is part of craft-application.
#
# Copyright 2023 Canonical Ltd.
#
#  This program is free software: you can redistribute it and/or modify it
#  under the terms of the GNU Lesser General Public License version 3, as
#  published by the Free Software Foundation.
#
#  This program is distributed in the hope that it will be useful, but WITHOUT
#  ANY WARRANTY; without even the implied warranties of MERCHANTABILITY,
#  SATISFACTORY QUALITY, or FITNESS FOR A PARTICULAR PURPOSE.
#  See the GNU Lesser General Public License for more details.
#
#  You should have received a copy of the GNU Lesser General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""Integration tests for project model."""
import pathlib

import pytest
import yaml

from craft_application import Project
from craft_application.errors import ProjectValidationError

VALID_YAML_DIR = pathlib.Path(__file__).parent / "project_files/valid"
INVALID_YAML_DIR = pathlib.Path(__file__).parent / "project_files/invalid"


@pytest.mark.parametrize("path", VALID_YAML_DIR.iterdir())
def test_from_file_valid_files(path):
    with path.open() as f:
        expected = yaml.safe_load(f)

    project = Project.from_file(path)
    marshalled = project.marshal()

    assert expected == marshalled


@pytest.mark.parametrize("path", INVALID_YAML_DIR.iterdir())
def test_from_file_invalid_files(path):
    with pytest.raises((ProjectValidationError, TypeError)):
        Project.from_file(path)
