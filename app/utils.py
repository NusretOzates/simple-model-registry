from typing import Dict

from pydantic.fields import FieldInfo


def pydantic_model_fields_to_str(model_fields: Dict[str, FieldInfo]) -> str:
    """ Pydantic model fields to string
    A helper function to convert Pydantic model fields to a string representation to be used in the API documentation.
    
    Args:
        model_fields: A dictionary of Pydantic model fields

    Returns:
        A string representation of the Pydantic model fields
    """
    field_descriptions = []

    for key, value in model_fields.items():
        value_type = value.annotation
        value_required = "required" if value.is_required() else "optional"
        field_descriptions.append(f"{key}: ({value_type}, {value_required})")

    return "\n\n" + "\n\n".join(field_descriptions)
