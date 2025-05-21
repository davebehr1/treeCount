from app.services.aerobotics_service import AeroboticsService
from app.services.missing_tree_imputer import MissingTreeImputer
from app.config import settings

def get_aerobotics_service() -> AeroboticsService:
    return AeroboticsService(settings)


def get_missing_tree_imputer() -> MissingTreeImputer:
    return MissingTreeImputer()
