from typing import List, Optional
from pydantic import BaseModel

class Survey(BaseModel):
    id: int
    orchard_id: int
    date: str
    hectares: float
    polygon: str


class SurveyResponse(BaseModel):
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[Survey]


class TreeSurvey(BaseModel):
    id: int
    lat: float
    lng: float
    ndre: float
    ndvi: float
    volume: float
    area: float
    row_index: Optional[int] = None
    tree_index: Optional[int] = None
    survey_id: int


class TreeSurveyResponse(BaseModel):
    count: int
    next: Optional[str]
    previous: Optional[str]
    results: List[TreeSurvey]
