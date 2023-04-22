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
"""General fixtures for tests."""
from unittest import mock

import pytest

from craft_application import utils


@pytest.fixture
def mock_confirm_with_user(monkeypatch):
    mock_fn = mock.Mock(spec=utils.confirm_with_user)
    monkeypatch.setattr(utils, "confirm_with_user", mock_fn)
    yield mock_fn
