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

from craft_application import utils, Project

import functools
from pathlib import Path
from unittest import mock

import craft_providers
import pytest
from overrides import override

from craft_application import Application, ProviderManager


class FakeApplication(Application):
    def generate_metadata(self) -> None:
        pass

    def create_package(self) -> Path:
        return Path()


class FakeProviderManager(ProviderManager):
    @override
    def get_configuration(self, *, base, instance_name) -> craft_providers.Base:
        pass

    @functools.cached_property
    def mock_provider(self):
        return mock.Mock(spec=craft_providers.Provider)


@pytest.fixture
def provider_manager():
    yield FakeProviderManager("test_app", provider_map={})


@pytest.fixture
def application(provider_manager):
    yield FakeApplication(
        "test_app",
        "0.0",
        "Summary",
        provider_manager,
        project_class=Project
    )


@pytest.fixture
def mock_confirm_with_user(monkeypatch):
    mock_fn = mock.Mock(spec=utils.confirm_with_user)
    monkeypatch.setattr(utils, "confirm_with_user", mock_fn)
    yield mock_fn
