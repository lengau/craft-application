import pathlib
import re
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple, Union

import craft_parts
import pydantic
import yaml
from pydantic import PrivateAttr, conlist, constr

from . import errors


class ProjectModel(pydantic.BaseModel):
    """Base model for snapcraft project classes."""

    class Config:  # pylint: disable=too-few-public-methods
        """Pydantic model configuration."""

        validate_assignment = True
        extra = "forbid"
        allow_mutation = True  # project is updated with adopted metadata
        allow_population_by_field_name = True
        alias_generator = lambda s: s.replace("_", "-")  # noqa: E731


# A workaround for mypy false positives
# see https://github.com/samuelcolvin/pydantic/issues/975#issuecomment-551147305
# fmt: off
if TYPE_CHECKING:
    UniqueStrList = List[str]
else:
    UniqueStrList = conlist(str, unique_items=True)
# fmt: on


class Project(ProjectModel):
    """Craft Application project definition."""

    name: constr(max_length=40)  # type: ignore
    title: Optional[constr(max_length=40)]  # type: ignore
    base: Optional[str]
    build_base: Optional[str]
    version: constr(max_length=32, strict=True)  # type: ignore
    contact: Optional[Union[str, UniqueStrList]]
    donation: Optional[Union[str, UniqueStrList]]
    issues: Optional[Union[str, UniqueStrList]]
    source_code: Optional[str]
    website: Optional[str]
    summary: Optional[constr(max_length=78)]  # type: ignore
    description: Optional[str]
    license: Optional[str]
    parts: Dict[str, Any]  # parts are handled by craft-parts

    @pydantic.validator("name")
    @classmethod
    def _validate_name(cls, name):
        if not re.match(r"^[a-z0-9-]*[a-z][a-z0-9-]*$", name):
            raise ValueError(
                "names can only use ASCII lowercase letters, numbers, and hyphens, "
                "and must have at least one letter"
            )

        if name.startswith("-"):
            raise ValueError("names cannot start with a hyphen")

        if name.endswith("-"):
            raise ValueError("names cannot end with a hyphen")

        if "--" in name:
            raise ValueError("names cannot have two hyphens in a row")

        return name

    @pydantic.validator("version")
    @classmethod
    def _validate_version(cls, version, values):
        if version and not re.match(
            r"^[a-zA-Z0-9](?:[a-zA-Z0-9:.+~-]*[a-zA-Z0-9+~])?$", version
        ):
            raise ValueError(
                "versions consist of upper- and lower-case alphanumeric characters, "
                "as well as periods, colons, plus signs, tildes, and hyphens. They cannot "
                "begin with a period, colon, plus sign, tilde, or hyphen. They cannot end "
                "with a period, colon, or hyphen"
            )

        return version

    @pydantic.validator("parts", each_item=True)
    @classmethod
    def _validate_parts(cls, item):
        """Verify each part (craft-parts will re-validate this)."""
        craft_parts.validate_part(item)
        return item

    @classmethod
    def unmarshal(cls, data: Dict[str, Any]) -> "Project":
        """Create and populate a new ``Project`` object from dictionary data.
        The unmarshal method validates entries in the input dictionary, populating
        the corresponding fields in the data object.
        :param data: The dictionary data to unmarshal.
        :return: The newly created object.
        :raise TypeError: If data is not a dictionary.
        """
        if not isinstance(data, dict):
            raise TypeError("Project data is not a dictionary")

        try:
            project = Project(**data)
        except pydantic.ValidationError as err:
            raise errors.ProjectValidationError(
                _format_pydantic_errors(err.errors())
            ) from err

        return project

    @classmethod
    def from_file(cls, project_file: pathlib.Path) -> "Project":
        """Create and populate a new ``Project`` object from ``project_file``."""
        if not project_file.exists():
            raise errors.ProjectFileMissing(
                f"Could not find project file {str(project_file)!r}"
            )
        with project_file.open() as project_stream:
            project_data = yaml.load(project_stream, Loader=_SafeLoader)

        return cls.unmarshal(project_data)

    def get_effective_base(self) -> str:
        """Return the base to use to create the snap."""
        effective_base = None

        if self.build_base is not None:
            effective_base = self.build_base
        elif self.base is not None:
            effective_base = self.base

        if effective_base is None:
            raise RuntimeError("Could not determine effective base")

        return effective_base


def _format_pydantic_errors(errors, *, file_name: str = "snapcraft.yaml"):
    """Format errors.
    Example 1: Single error.
    Bad snapcraft.yaml content:
    - field: <some field>
      reason: <some reason>
    Example 2: Multiple errors.
    Bad snapcraft.yaml content:
    - field: <some field>
      reason: <some reason>
    - field: <some field 2>
      reason: <some reason 2>
    """
    combined = [f"Bad {file_name} content:"]
    for error in errors:
        formatted_loc = _format_pydantic_error_location(error["loc"])
        formatted_msg = _format_pydantic_error_message(error["msg"])

        if formatted_msg == "field required":
            field_name, location = _printable_field_location_split(formatted_loc)
            combined.append(
                f"- field {field_name} required in {location} configuration"
            )
        elif formatted_msg == "extra fields not permitted":
            field_name, location = _printable_field_location_split(formatted_loc)
            combined.append(
                f"- extra field {field_name} not permitted in {location} configuration"
            )
        elif formatted_msg == "the list has duplicated items":
            field_name, location = _printable_field_location_split(formatted_loc)
            combined.append(
                f" - duplicate entries in {field_name} not permitted in {location} configuration"
            )
        elif formatted_loc == "__root__":
            combined.append(f"- {formatted_msg}")
        else:
            combined.append(f"- {formatted_msg} (in field {formatted_loc!r})")

    return "\n".join(combined)


def _format_pydantic_error_location(loc):
    """Format location."""
    loc_parts = []
    for loc_part in loc:
        if isinstance(loc_part, str):
            loc_parts.append(loc_part)
        elif isinstance(loc_part, int):
            # Integer indicates an index. Go
            # back and fix up previous part.
            previous_part = loc_parts.pop()
            previous_part += f"[{loc_part}]"
            loc_parts.append(previous_part)
        else:
            raise RuntimeError(f"unhandled loc: {loc_part}")

    loc = ".".join(loc_parts)

    # Filter out internal __root__ detail.
    loc = loc.replace(".__root__", "")
    return loc


def _format_pydantic_error_message(msg):
    """Format pydantic's error message field."""
    # Replace shorthand "str" with "string".
    msg = msg.replace("str type expected", "string type expected")
    return msg


def _printable_field_location_split(location: str) -> Tuple[str, str]:
    """Return split field location.
    If top-level, location is returned as unquoted "top-level".
    If not top-level, location is returned as quoted location, e.g.
    (1) field1[idx].foo => 'foo', 'field1[idx]'
    (2) field2 => 'field2', top-level
    :returns: Tuple of <field name>, <location> as printable representations.
    """
    loc_split = location.split(".")
    field_name = repr(loc_split.pop())

    if loc_split:
        return field_name, repr(".".join(loc_split))

    return field_name, "top-level"


def _check_duplicate_keys(node):
    mappings = set()

    for key_node, _ in node.value:
        try:
            if key_node.value in mappings:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate key {key_node.value!r}",
                    node.start_mark,
                )
            mappings.add(key_node.value)
        except TypeError:
            # Ignore errors for malformed inputs that will be caught later.
            pass


def _dict_constructor(loader, node):
    _check_duplicate_keys(node)

    # Necessary in order to make yaml merge tags work
    loader.flatten_mapping(node)
    value = loader.construct_pairs(node)

    try:
        return dict(value)
    except TypeError as type_error:
        raise yaml.constructor.ConstructorError(
            "while constructing a mapping",
            node.start_mark,
            "found unhashable key",
            node.start_mark,
        ) from type_error


class _SafeLoader(yaml.SafeLoader):  # pylint: disable=too-many-ancestors
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _dict_constructor
        )
