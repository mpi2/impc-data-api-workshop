from pydantic import BaseModel, model_validator
import json
from typing import List, Dict
from pathlib import Path
import warnings

CORE_FILE = Path('impc_api_helper', 'impc_api_helper', 'utils', 'core_fields.json')

# Define the dictionary with available options: core:fields
def load_core_fields(filename: Path):
    with open(filename, "r") as f:
        validation_dict = json.load(f)
    return validation_dict

# Define the validation dict
validation_json = load_core_fields(CORE_FILE)

# Function to parse the fields (fl) params in params
def get_fields(fields: str) -> List[str]:
    return fields.split(",")


class CoreParamsValidator(BaseModel):
    core: str
    params: Dict

    @model_validator(mode='before')
    @classmethod
    def validate_core_and_fields(cls, values):
        core = values.get("core")
        params = values.get("params")

        # Validate core
        if core not in validation_json.keys():
            raise ValueError(f'Invalid core: "{core}", select from the available:\n{validation_json.keys()})')

        # Compare passed fl values vs the allowed fl values for a given core
        fields: str = params.get("fl")

        # If no fields were specified, pass
        if fields is None:
            print("No fields passed, skipping field validation...")
            return values

        # Get the fields passed to params and the expected fields for the core
        field_list: List[str] = get_fields(fields)
        accepted_core_fields: List[str] = validation_json.get(core, [])

        # Validate each field in params
        for fl in field_list:
            if fl not in accepted_core_fields:
                warnings.warn(f'Invalid field: "{fl}". Check spelling of fields. To see available fields check the documentation at: https://www.ebi.ac.uk/mi/impc/solrdoc/',
                              category=UserWarning)
        # Return validated values
        return values

# Check and raise error as needed.
