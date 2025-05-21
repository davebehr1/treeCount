from typing import List, Dict, Any, Tuple
import httpx
from shapely.geometry import Polygon
from app.config import Settings
from app.models.orchard_models import (
    SurveyResponse,
    TreeSurveyResponse,
)

class AeroboticsService:
    def __init__(self, settings: Settings):
        self.base_url = "https://api.aerobotics.com/farming/"
        self.headers = {
            "Authorization": f"Bearer {settings.auth_token}",
            "accept": "application/json"
        }


    async def fetch_polygon_and_tree_locations(self,orchard_id: int) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            survey_resp = await client.get(
                f"{self.base_url}surveys/", headers=self.headers, params={"orchard_id": orchard_id}
            )
            survey_resp.raise_for_status()
            surveys = SurveyResponse(**survey_resp.json())

            if not surveys.results:
                raise ValueError(f"No surveys found for orchard ID {orchard_id}")

            survey = surveys.results[0]
            polygon = survey.polygon
            survey_id = survey.id

            tree_resp = await client.get(
                f"{self.base_url}surveys/{survey_id}/tree_surveys/", headers=self.headers
            )
            tree_resp.raise_for_status()
            tree_data = TreeSurveyResponse(**tree_resp.json())

            return {
                "polygon": self.__parse_polygon_string_to_coords(polygon),
                "tree_locations": self.__extract_locations_from_tree_survey(tree_data),
            }


    def __parse_polygon_string_to_coords(self,polygon_str: str) -> Polygon:
        coord_pairs = polygon_str.strip().split()

        coords = [
            (float(lon), float(lat))
            for lon, lat in (pair.split(",") for pair in coord_pairs)
        ]

        return Polygon(coords)


    def __extract_locations_from_tree_survey(self, tree_survey_response: TreeSurveyResponse) -> List[Tuple[float, float, float]]:
        locations = []

        for tree in tree_survey_response.results:
            lat = tree.lat
            lng = tree.lng
            area = tree.area

            locations.append((lng, lat, area))

        return locations
