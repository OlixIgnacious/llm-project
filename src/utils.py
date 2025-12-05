from typing import Dict, Any, Tuple
from pydantic import BaseModel, ValidationError
from .schemas import StartupAssessment

def validate_output(obj: dict) -> Tuple[bool, Any]:
    """
    Validate a dictionary against the StartupAssessment schema.

    Args:
        obj (dict): The dictionary to validate.

    Returns:
        Tuple[bool, Any]: A tuple where the first element is a boolean indicating
                          if validation was successful, and the second element is
                          either the validated StartupAssessment instance or the
                          validation error.
    """
    try:
        assessment = StartupAssessment.model_validate(obj)
        return True, assessment
    except ValidationError as e:
        return False, e