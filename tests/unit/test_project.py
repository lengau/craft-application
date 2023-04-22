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
"""Tests for project model."""
import pathlib
import re
from string import ascii_lowercase, digits, ascii_letters

import pytest
import yaml
from hypothesis.provisional import urls
from pydantic import ValidationError

from craft_application.errors import ProjectValidationError
from craft_application.project import Project
from hypothesis import given, strategies

ALPHA_NUMERIC = [*ascii_letters, *digits]
LOWER_ALPHA_NUMERIC = [*ascii_lowercase, *digits]
VERSION_STRING_VALID_CHARACTERS = [*ascii_letters, *digits, *":.+~-"]
INVALID_BASES = ("", "1", "   ")


# region Hypothesis strategies
@strategies.composite
def valid_project_name_strategy(draw):
    """A strategy for a project name that matches all the project name rules:

    * Valid characters are lower-case ASCII letters, numerals and hyphens.
    * Must contain at least one letter
    * May not start or end with a hyphen
    * May not have two hyphens in a row
    """
    strategy = strategies.text(
        strategies.sampled_from([*LOWER_ALPHA_NUMERIC, "-"]),
        min_size=1,
        max_size=40
    )
    filtered = strategy.filter(
        lambda name: all(
            (
                "--" not in name,
                not (name.startswith("-") or name.endswith("-")),
                re.match("[a-z]", name),
            )
        )
    )
    return draw(filtered)


def valid_title_strategy():
    return strategies.text(max_size=40).filter(lambda txt: len(txt.strip()) >= 2)


def valid_base_strategy():
    return strategies.text(
        [*LOWER_ALPHA_NUMERIC, "-"],
        max_size=40
    ).filter(lambda base: len(base.strip()) >= 2)


def valid_version_strategy():
    return strategies.text(
        strategies.sampled_from(VERSION_STRING_VALID_CHARACTERS),
        min_size=1,
        max_size=32,
    ).filter(
        lambda version: version[0] in ALPHA_NUMERIC and version[-1] not in "-:."
    )


def optional_string_or_unique_list():
    return strategies.one_of(
        strategies.none(),
        strategies.text(),
        strategies.lists(strategies.text(), unique=True)
    )


# endregion
# region Validation tests
@given(name=valid_project_name_strategy())
def test_valid_name_hypothesis(name):
    Project(name=name, version="0.0", parts={})


@pytest.mark.parametrize("name", [" ab "])
def test_valid_name(name):
    Project(name=name, version="0.0", parts={})

@pytest.mark.parametrize(
    "name",
    ["", "-starts-with-hyphen", "ends-with-hyphen-", "two--hyphens"]
)
def test_invalid_name(name):
    with pytest.raises(ValidationError):
        Project(name=name, version="0.0", parts={})


@given(valid_title_strategy())
def test_valid_title_hypothesis(title):
    Project(title=title, name="name", version="0.0", parts={})


@pytest.mark.parametrize("title", ["", "1", "  ", "A" * 41])
def test_invalid_title(title):
    with pytest.raises(ValidationError):
        Project(title=title, name="name", version="0.0", parts={})


@given(valid_base_strategy())
def test_valid_base(base):
    Project(base=base, name="name", version="0.0", parts={})


@pytest.mark.parametrize("base", INVALID_BASES)
def test_invalid_base(base):
    with pytest.raises(ValidationError):
        Project(base=base, name="name", version="0.0", parts={})


@given(valid_base_strategy())
def test_valid_build_base(base):
    Project(build_base=base, name="name", version="0.0", parts={})


@pytest.mark.parametrize("base", INVALID_BASES)
def test_invalid_base(base):
    with pytest.raises(ValidationError):
        Project(build_base=base, name="name", version="0.0", parts={})


@given(valid_version_strategy())
def test_valid_version_hypothesis(version):
    Project(version=version, name="name", parts={})


@pytest.mark.parametrize(
    "version",
    [":a", "a:", ".a", "a.", "-a", "a-", "+a", "~a"]
)
def test_invalid_version(version):
    with pytest.raises(ValidationError):
        Project(version=version, name="name", parts={})
# endregion
# region Constructor tests
@given(
    name=valid_project_name_strategy(),
    title=strategies.one_of(strategies.none(), valid_title_strategy()),
    base=strategies.one_of(strategies.none(), valid_base_strategy()),
    build_base=strategies.one_of(strategies.none(), valid_base_strategy()),
    version=valid_version_strategy(),
    contact=optional_string_or_unique_list(),
    donation=optional_string_or_unique_list(),
    issues=optional_string_or_unique_list(),
    source_code=strategies.sampled_from([None, "git+ssh://git.launchpad.net/project"]),
    website=strategies.sampled_from([None, "https://canonical.com"]),
    summary=strategies.one_of(strategies.none(), strategies.text(max_size=78)),
    description=strategies.one_of(strategies.none(), strategies.text()),
    license=strategies.one_of(strategies.none(), strategies.text()),
)
def test_marshal_unmarshal(
    name, title, base, build_base, version, contact, donation, issues, source_code,
    website, summary, description, license
):
    project = Project(
        name=name, title=title, base=base, build_base=build_base, version=version,
        contact=contact, donation=donation, issues=issues, source_code=source_code,
        website=website, summary=summary, description=description, license=license,
        parts={}
    )
    new_project = Project.unmarshal(project.marshal())

    assert project == new_project

@given(
    name=valid_project_name_strategy(),
    title=strategies.one_of(strategies.none(), valid_title_strategy()),
    base=strategies.one_of(strategies.none(), valid_base_strategy()),
    build_base=strategies.one_of(strategies.none(), valid_base_strategy()),
    version=valid_version_strategy(),
    contact=optional_string_or_unique_list(),
    donation=optional_string_or_unique_list(),
    issues=optional_string_or_unique_list(),
    source_code=strategies.sampled_from([None, "git+ssh://git.launchpad.net/project"]),
    website=strategies.sampled_from([None, "https://canonical.com"]),
    summary=strategies.one_of(strategies.none(), strategies.text(max_size=78)),
    description=strategies.one_of(strategies.none(), strategies.text()),
    license=strategies.one_of(strategies.none(), strategies.text()),
)
def test_unmarshal_marshal(
    name, title, base, build_base, version, contact, donation, issues, source_code,
    website, summary, description, license
):
    project_dict = {
        "name": name, "title": title, "base": base, "build-base": build_base,
        "version": version, "contact": contact, "donation": donation,
        "issues": issues, "source-code": source_code, "website": website,
        "summary": summary, "description": description, "license": license,
        "parts": {}
    }
    expected = project_dict.copy()
    if title is not None:
        expected["title"] = title.strip()
    if summary is not None:
        expected["summary"] = summary.strip()

    marshalled = Project.unmarshal(project_dict).marshal()

    assert marshalled == expected
# endregion


@pytest.mark.parametrize(
    ["base", "build_base", "expected"],
    [
        (None, "build_base", "build_base"),
        ("base", None, "base"),
        ("base", "build_base", "build_base"),
    ]
)
def test_effective_base_success(base, build_base, expected):
    project = Project(
        name="name", version="0.0", parts={},
        base=base, build_base=build_base
    )

    assert project.effective_base == expected


def test_effective_base_error():
    project = Project(name="name", version="0.0", parts={})

    with pytest.raises(RuntimeError):
        return project.effective_base
