from pydantic import BaseModel, model_validator
import json
from typing import List, Dict
from pathlib import Path
import warnings
from dataclasses import dataclass, field
from impc_api_helper.utils.warnings import warning_config, InvalidCoreWarning, InvalidFieldWarning

# Initialise warning config
warning_config()

# Dataclass for the json validator
@dataclass
class ValidationJson:
    CORE_FILE: Path = Path(__file__).resolve().parent / 'core_fields.json'
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

    @model_validator(mode='before')
    @classmethod
    def validate_core_and_fields(cls, values):
        core = values.get("core")
        params = values.get("params")

        # Call the Validator Object
        jv = ValidationJson()

        # Validate core
        if core not in jv.valid_cores():
            warnings.warn(
                message=f'Invalid core: "{core}", select from the available cores:\n{jv.valid_cores()})\n',
                category=InvalidCoreWarning)

        # Compare passed fl values vs the allowed fl values for a given core
        fields: str = params.get("fl")

        # If no fields were specified, pass
        if fields is None:
            print("No fields passed, skipping field validation...")
            return values

        # Get the fields passed to params and the expected fields for the core
        field_list: List[str] = get_fields(fields)


        # Validate each field in params
        # TODO: perhaps pass al invalid fields as a list, instead of many warning messages
        for fl in field_list:
            if fl not in jv.valid_fields(core):
                warnings.warn(message=f"""Unexpected field name: "{fl}". Check the spelling of fields.\nTo see expected fields check the documentation at: https://www.ebi.ac.uk/mi/impc/solrdoc/""",
                category=InvalidFieldWarning)
        # Return validated values
        return values




