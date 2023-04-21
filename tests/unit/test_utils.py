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
"""Tests for generic utility functions."""
import builtins
import os
import sys
from unittest import mock

import pytest
from hypothesis import given, strategies

from craft_application.errors import CraftEnvironmentError
from craft_application.utils import get_env_bool, confirm_with_user, FALSEY_STRINGS, \
    TRUTHY_STRINGS, TRUTH_VALUE_STRINGS


# region get_env_bool
@pytest.mark.parametrize(
    ["var", "value", "expected"],
    [
        ("Env_Var", "y", True),
        ("TRUTHY", "YeS", True),
        ("THIS_IS_AN_ENVIRONMENT_VARIABLE", "TRUE", True),
        ("Light Switch", "on", True),
        ("one", "1", True),
        ("empty", "", False),
        ("LETTER_N", "N", False),
        ("lolno", "no", False),
        ("blargh_off", "Off", False),
        ("Zero!", "0", False),
    ]
)
def test_get_env_bool_true_false(var, value, expected):
    with pytest.MonkeyPatch.context() as mp:
        mp.setenv(var, value)

        actual = get_env_bool(var)

    assert actual == expected


@pytest.mark.parametrize("var", "ENV_VAR")
def test_get_env_bool_unset(var):
    with pytest.MonkeyPatch.context() as mp:
        mp.delenv(var, raising=False)  # Ensure the variable isn't set.

        actual = get_env_bool(var)

    assert actual is None


@given(
    var=strategies.text(
        alphabet=strategies.sampled_from("ABCDEFGHIJKLMNOPQRSTUVWXYZ_"),
        min_size=1
    ),
    value=strategies.text(
        alphabet=strategies.characters(blacklist_categories="C"),
        min_size=1
    ).filter(lambda x: x not in TRUTH_VALUE_STRINGS)
)
def test_get_env_bool_error(var, value):
    with pytest.MonkeyPatch.context() as mp:
        mp.setitem(os.environ, var, value)

        with pytest.raises(CraftEnvironmentError) as exc_info:
            get_env_bool(var)

    assert exc_info.value.args[0] == f"Invalid value in environment variable {var}"
    assert exc_info.value.reportable is False
# endregion
# region confirm_with_user
@given(
    default=strategies.booleans(),
    prompt=strategies.text(min_size=1)
)
def test_confirm_with_user_noninteractive(prompt, default):
    mock_isatty = mock.Mock(return_value=False)
    mock_input = mock.Mock()
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(sys.stdin, "isatty", mock_isatty)
        mp.setattr(builtins, "input", mock_input)

        actual = confirm_with_user(prompt, default=default)

    assert actual == default
    mock_isatty.assert_called_once_with()
    mock_input.assert_not_called()


@pytest.mark.parametrize(
    ["user_input", "default", "expected"],
    [
        pytest.param("y", True, True, id="basic_true"),
        pytest.param("Y", True, True, id="upper_true"),
        pytest.param("y", False, True, id="basic_true_non_default"),
        pytest.param("Y", False, True, id="upper_true_non_default"),
        pytest.param("n", False, False, id="basic_false"),
        pytest.param("N", False, False, id="upper_false"),
        pytest.param("n", True, False, id="basic_false_non_default"),
        pytest.param("N", True, False, id="upper_false_non_default"),
        pytest.param("", True, True, id="default_true"),
        pytest.param("", False, False, id="default_false"),
        pytest.param("Yep", False, True, id="starts_with_Y"),
        pytest.param("yep", False, True, id="starts_with_y"),
        pytest.param("Nope!", True, False, id="starts_with_N"),
        pytest.param("nuh uh", True, False, id="starts_with_n"),
    ]
)
def test_confirm_with_user_interactive(user_input, default, expected):
    mock_isatty = mock.Mock(return_value=True)
    mock_input = mock.Mock(return_value=user_input)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(sys.stdin, "isatty", mock_isatty)
        mp.setattr(builtins, "input", mock_input)

        actual = confirm_with_user("Prompt", default=default)

    assert actual == expected
    mock_isatty.assert_called_once_with()
    mock_input.assert_called_once()
# endregion
