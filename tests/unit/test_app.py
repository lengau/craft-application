#  This file is part of craft-application.
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
"""App tests."""
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    ["is_managed", "expected"],
    [
        (True, Path("/tmp/test_app.log")),
        (False, None),
    ]
)
def test_log_path(application, is_managed, expected):
    application._manager.is_managed = is_managed

    actual = application.log_path

    assert actual == expected



