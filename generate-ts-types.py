#!/usr/bin/env python

"""Generate TypeScript type definitions from Pydantic models for the Vue frontend."""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import TypeGuard

from pydantic import BaseModel, RootModel, TypeAdapter
from pydantic.json_schema import GenerateJsonSchema, JsonSchemaValue
from pydantic_core import core_schema

from questionpy_common.elements import OptionsFormDefinition
from questionpy_common.manifest import Manifest
from questionpy_sdk.webserver.controllers.attempt.data import AttemptRenderData
from questionpy_sdk.webserver.controllers.attempt.errors import ErrorSectionKey
from questionpy_sdk.webserver.controllers.attempt.question_ui import ClientQuestionDisplayOptions
from questionpy_sdk.webserver.controllers.question.controller import OptionsStateResponse
from questionpy_sdk.webserver.middlewares.error import DetailedServerError

logging.basicConfig(level=logging.INFO, format="")
logger = logging.getLogger(__name__)

# Types exposed to the client
TYPES: tuple[type[BaseModel] | TypeAdapter, ...] = (
    TypeAdapter(AttemptRenderData),
    ClientQuestionDisplayOptions,
    TypeAdapter(DetailedServerError),
    TypeAdapter(ErrorSectionKey),
    Manifest,
    OptionsFormDefinition,
    TypeAdapter(OptionsStateResponse),
)

SCRIPT_PATH = Path(__file__).parent
FRONTEND_PATH = SCRIPT_PATH / "frontend"
TYPES_PATH = FRONTEND_PATH / "src" / "types"

type CoreSchemaOrField = (
    core_schema.CoreSchema
    | core_schema.ModelField
    | core_schema.DataclassField
    | core_schema.TypedDictField
    | core_schema.ComputedField
)

type PrimitiveSchema = (
    core_schema.AnySchema
    | core_schema.NoneSchema
    | core_schema.BoolSchema
    | core_schema.IntSchema
    | core_schema.FloatSchema
    | core_schema.DecimalSchema
    | core_schema.StringSchema
    | core_schema.BytesSchema
    | core_schema.DateSchema
    | core_schema.TimeSchema
    | core_schema.DatetimeSchema
    | core_schema.TimedeltaSchema
    | core_schema.LiteralSchema
    | core_schema.UrlSchema
    | core_schema.MultiHostUrlSchema
    | core_schema.UuidSchema
)


def is_primitive_field(schema: CoreSchemaOrField) -> TypeGuard[PrimitiveSchema]:
    return schema["type"] in {
        "any",
        "none",
        "bool",
        "int",
        "float",
        "decimal",
        "str",
        "bytes",
        "date",
        "time",
        "datetime",
        "timedelta",
        "literal",
        "url",
        "multi-host-url",
        "uuid",
    }


def is_union_field(schema: CoreSchemaOrField) -> TypeGuard[core_schema.UnionSchema]:
    return schema["type"] == "union"


def is_list_like_schema_with_items_schema(
    schema: CoreSchemaOrField,
) -> TypeGuard[core_schema.ListSchema | core_schema.SetSchema | core_schema.FrozenSetSchema]:
    return schema["type"] in {"list", "set", "frozenset"}


class TypeScriptSchemaGenerator(GenerateJsonSchema):
    def model_schema(self, schema: core_schema.ModelSchema) -> JsonSchemaValue:
        """Mark all properties with default values as required.

        Since API output schemas always include defaults, these fields should be required.
        """
        json_schema = super().model_schema(schema)
        cls = schema["cls"]

        if issubclass(cls, BaseModel):
            # Skip RootModel since it's unwrapped in JSON Schema
            if issubclass(cls, RootModel):
                return json_schema

            model_fields = cls.model_fields
            properties = json_schema.get("properties", {})
            required = set(json_schema.get("required", []))

            for field_name, field_info in model_fields.items():
                if field_name not in properties:
                    continue  # Skip excluded fields

                if field_info.default is not core_schema.PydanticUndefined or field_info.default_factory is not None:
                    required.add(field_name)

            if required:
                json_schema["required"] = sorted(required)

        return json_schema

    def field_title_should_be_set(self, schema: CoreSchemaOrField) -> bool:
        """Avoid setting the title field for simple types to force inline type definitions.

        This prevents excessive and unnecessary type definitions in the generated output, allowing the downstream
        TypeScript converter to inline these types instead.
        """
        if is_primitive_field(schema):
            return False

        if is_union_field(schema):
            return not any(
                is_primitive_field(s[0]) if isinstance(s, tuple) else is_primitive_field(s) for s in schema["choices"]
            )

        if is_list_like_schema_with_items_schema(schema):
            inner_schema = schema.get("items_schema", core_schema.any_schema())
            return self.field_title_should_be_set(inner_schema)

        return super().field_title_should_be_set(schema)


async def write_ts_definitions(validatable: type[BaseModel] | TypeAdapter, *, write_json_schema: bool = False) -> Path:
    """Write TypeScript definitions for a model or type.

    Generates a JSON schema and passes it to the `json-schema-to-types.ts` script to produce a
    corresponding `SCHEMA_TITLE.generated.ts` file.

    Args:
        validatable: A Pydantic model class or TypeAdapter instance.
        write_json_schema: Whether to write intermediate JSON Schema files during processing.

    Returns:
        Relative path to the generated TypeScript file.
    """
    # Wrap models in TypeAdapter to unify interface
    validatable = validatable if isinstance(validatable, TypeAdapter) else TypeAdapter(validatable)
    schema = validatable.json_schema(schema_generator=TypeScriptSchemaGenerator, mode="serialization")

    if write_json_schema:
        (SCRIPT_PATH / f"{schema['title']}.schema.json").write_text(json.dumps(schema))

    # Run TypeScript generator and capture output
    proc = await asyncio.create_subprocess_exec(
        "npm",
        "exec",
        "tsx",
        "json-schema-to-types.ts",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=FRONTEND_PATH,
    )
    stdout, stderr = await proc.communicate(json.dumps(schema).encode())
    if proc.returncode != 0:
        msg = f"Error generating type {schema['title']}. The output was:\n{stderr.decode()}"
        raise RuntimeError(msg)

    # Write TypeScript definitions to file
    output_path = TYPES_PATH / f"{schema['title']}.generated.ts"
    output_path.write_text(stdout.decode())

    return output_path.relative_to(SCRIPT_PATH)


async def main() -> int:
    write_json_schema = "--write-json-schema" in sys.argv
    TYPES_PATH.mkdir(exist_ok=True)
    tasks = (write_ts_definitions(t, write_json_schema=write_json_schema) for t in TYPES)
    return_code: int = os.EX_OK
    for result in await asyncio.gather(*tasks, return_exceptions=True):
        if isinstance(result, Exception):
            logger.error("Task failed:", exc_info=result)
            return_code = os.EX_SOFTWARE
        else:
            logger.info("Generated: %s", result)
    return return_code


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
