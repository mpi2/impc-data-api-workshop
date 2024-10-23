"""
This module provides validation for core fields and download formats using Pydantic models. 

Classes:
    - ValidationJson: Loads and validates core fields from a JSON configuration file.
    - CoreParamsValidator: Validates core names and associated fields (fl), issuing warnings for invalid inputs.
    - DownloadFormatValidator: Validates the download format (wt) to ensure it is supported (json or csv).

Functions:
    - get_fields(fields: str) -> List[str]: Parses a comma-separated string of field names into a list.

Custom Exceptions:
    - InvalidCoreWarning: Raised for invalid core names.
    - InvalidFieldWarning: Raised for unexpected field names.
    - UnsupportedDownloadFormatError: Raised for unsupported download formats.
"""

import json
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict
from pydantic import BaseModel, model_validator, field_validator
from impc_api.utils.warnings import (
    warning_config,
    InvalidCoreWarning,
    InvalidFieldWarning,
    UnsupportedDownloadFormatError,
)

# Initialise warning config
warning_config()

# Dataclass for the json validator
@dataclass
class ValidationJson:
    CORE_FILE: Path = Path(__file__).resolve().parent / "core_fields.json"
    _validation_json: Dict[str, List[str]] = field(default_factory=dict, init=False)

    # Eager initialisation
    def __post_init__(self):
        self._validation_json = self.load_core_fields(self.CORE_FILE)

    def load_core_fields(self, filename: Path) -> Dict[str, List[str]]:
        with open(filename, "r") as f:
            return json.load(f)

    def valid_cores(self):
        return self._validation_json.keys()

    def valid_fields(self, core: str) -> List[str]:
        return self._validation_json.get(core, [])


# Function to parse the fields (fl) params in params
def get_fields(fields: str) -> List[str]:
    return fields.split(",")


class CoreParamsValidator(BaseModel):
    core: str
    params: Dict

    @model_validator(mode="before")
    @classmethod
    def validate_core_and_fields(cls, values):
        invalid_core: bool = False
        core = values.get("core")
        params = values.get("params")

        # Call the Validator Object
        jv = ValidationJson()

        # Validate core
        if core not in jv.valid_cores():
            invalid_core = True
            warnings.warn(
                message=f'Invalid core: "{core}", select from the available cores:\n{jv.valid_cores()})\n',
                category=InvalidCoreWarning,
            )

        # Compare passed fl values vs the allowed fl values for a given core
        fields: str = params.get("fl")

        # If no fields were specified, pass
        if fields is None:
            print("No fields passed, skipping field validation...")
            return values

        # Get the fields passed to params and the expected fields for the core
        field_list: List[str] = get_fields(fields)

        # Validate each field in params
        if invalid_core is not True:
            for fl in field_list:
                if fl not in jv.valid_fields(core):
                    warnings.warn(
                        message=f"""Unexpected field name: "{fl}". Check the spelling of fields.\nTo see expected fields check the documentation at: https://www.ebi.ac.uk/mi/impc/solrdoc/""",
                        category=InvalidFieldWarning,
                    )
        # Return validated values
        return values


class DownloadFormatValidator(BaseModel):
    """Validates params["wt"] from a batch_request"""

    wt: str

    @field_validator("wt")
    def validate_wt(cls, value):
        supported_formats = {"json", "csv"}
        if value not in supported_formats:
            raise UnsupportedDownloadFormatError(
                f"Unsupported format '{value}'. Only {supported_formats} are supported for download."
            )
        return value
