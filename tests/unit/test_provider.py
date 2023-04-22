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
"""Tests for provider manager."""
import functools
import os
import sys
from unittest import mock

import craft_providers
import pytest
from craft_cli import CraftError
from craft_providers import lxd, multipass
from overrides import override

from craft_application import ProviderManager, utils


class FakeProviderManager(ProviderManager):
    @override
    def get_configuration(self, *, base, instance_name) -> craft_providers.Base:
        pass

    @functools.cached_property
    def mock_provider(self):
        return mock.Mock(spec=craft_providers.Provider)


@pytest.fixture
def fake_manager(monkeypatch):
    fake_manager = FakeProviderManager("test_app", provider_map={})
    fake_manager.provider_map = {"test_provider": lambda: fake_manager.mock_provider}
    monkeypatch.setenv(fake_manager.provider_env, "test_provider")
    yield fake_manager


@pytest.mark.parametrize(
    ["app_name", "managed_mode_env", "expected"],
    [
        ("test", None, "TEST_MANAGED_MODE"),
        ("test", "", "TEST_MANAGED_MODE"),
        ("test", "AnY_vArIaBlE_nAmE", "AnY_vArIaBlE_nAmE")
    ]
)
def test_init_managed_mode_env(app_name, managed_mode_env, expected):
    manager = FakeProviderManager(app_name, provider_map={}, managed_mode_env=managed_mode_env)

    assert manager.managed_mode_env == expected


@pytest.mark.parametrize(
    ["app_name", "provider_env", "expected"],
    [
        ("test", None, "TEST_PROVIDER"),
        ("test", "", "TEST_PROVIDER"),
        ("test", "AnY_vArIaBlE_nAmE", "AnY_vArIaBlE_nAmE")
    ]
)
def test_init_provider_env(app_name, provider_env, expected):
    manager = FakeProviderManager(app_name, provider_map={}, provider_env=provider_env)

    assert manager.provider_env == expected


@pytest.mark.parametrize(
    ["platform", "provider_class"],
    [
        ("linux", lxd.LXDProvider),
        ("Not Linux", multipass.MultipassProvider),
    ]
)
def test_get_default_provider(fake_manager, platform, provider_class):
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(sys, "platform", platform)

        actual = fake_manager._get_default_provider()

    assert isinstance(actual, provider_class)


@pytest.mark.parametrize(
    ["env_bool", "expected"], [(True, True), (False, False), (None, False)]
)
def test_is_managed(fake_manager, env_bool, expected):
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(utils, "get_env_bool", lambda _: env_bool)

        actual = fake_manager.is_managed

    assert actual == expected


# region get_provider tests
def test_get_provider_managed(fake_manager):
    fake_manager.is_managed = True

    with pytest.raises(CraftError) as exc_info:
        fake_manager.get_provider()

    assert exc_info.value.args[0] == "Cannot nest managed environments."


def test_get_provider_no_environment(monkeypatch, fake_manager):
    monkeypatch.delenv(fake_manager.provider_env, raising=False)
    mock_provider = mock.Mock()
    monkeypatch.setattr(fake_manager, "_get_default_provider", lambda: mock_provider)

    provider = fake_manager.get_provider()

    assert provider == mock_provider


def test_get_provider_is_installed(fake_manager):
    fake_manager.mock_provider.is_provider_installed.return_value = True

    actual = fake_manager.get_provider()

    assert actual == fake_manager.mock_provider


def test_get_provider_auto_install(mock_confirm_with_user, fake_manager):
    fake_manager.mock_provider.is_provider_installed.return_value = False
    fake_manager.mock_provider.ensure_provider_is_available = mock.Mock()
    mock_confirm_with_user.return_value = True

    fake_manager.get_provider()

    fake_manager.mock_provider.ensure_provider_is_available.assert_called_once_with()
    mock_confirm_with_user.assert_called_once()


def test_get_provider_no_auto_install(mock_confirm_with_user, fake_manager):
    fake_manager.mock_provider.is_provider_installed.return_value = False
    mock_confirm_with_user.return_value = False

    with pytest.raises(CraftError) as exc_info:
        fake_manager.get_provider()

    assert exc_info.value.args[0] == "Cannot proceed without test_provider installed."
    assert exc_info.value.resolution == "Install test_provider and run again."
# endregion
