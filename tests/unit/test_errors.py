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
"""Tests for error classes."""
import pytest
from pytest_check import check
from craft_parts import PartsError
from hypothesis import given, strategies

from craft_application.errors import PartsLifecycleError, CraftEnvironmentError


@given(
    message=strategies.text(),
    details=strategies.text(),
    resolution=strategies.text()
)
def test_parts_lifecycle_error(message, details, resolution):
    parts_error = PartsError(message, details, resolution)

    lifecycle_error = PartsLifecycleError.from_parts_error(parts_error)

    check.equal(lifecycle_error.args[0], message)
    check.equal(lifecycle_error.details, details)
    check.equal(lifecycle_error.resolution, resolution)


@pytest.mark.parametrize(
    ["variable", "value", "valid_values", "message", "details"],
    [
        pytest.param(
            "VAR_NAME", "Some_Value", ["a", "b"],
            "Invalid value in environment variable VAR_NAME",
            "Value could not be parsed: 'Some_Value'\nValid values: 'a', 'b'"
        )
    ]
)
def test_environment_error(variable, value, valid_values, message, details):
    error = CraftEnvironmentError(
        variable, value, valid_values=valid_values
    )

    check.equal(error.args[0], message)
    check.equal(error.details, details)
