from fastapi import FastAPI, Path, HTTPException, Depends
from fastapi.responses import FileResponse
from app.services.aerobotics_service import AeroboticsService
from app.services.missing_tree_imputer import MissingTreeImputer
from app.exceptions.handler import http_exception_handler
from app.dependencies import get_aerobotics_service, get_missing_tree_imputer
from app.config import logger
from typing import List, Tuple
from shapely.geometry import Polygon
import os

app = FastAPI(
    title="Missing Tree Count API",
    description="API for detecting and imputing missing trees in orchards using geospatial data.",
    version="1.0.0",
    docs_url="/docs"
)

app.add_exception_handler(HTTPException, http_exception_handler)

@app.get("/orchards/{orchard_id}/missing-trees", summary="Get Missing Trees")
async def missing_tree_locations(
    orchard_id:int = Path(..., example=216269, description="ID of orchard"),
    aerobotics_service: AeroboticsService = Depends(get_aerobotics_service),
    missing_tree_imputer_service: MissingTreeImputer = Depends(get_missing_tree_imputer)
    ):
    """
    Imputes missing tree locations.
    """
    try:
        response_data = await aerobotics_service.fetch_polygon_and_tree_locations(orchard_id)
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=f"Bad request: {str(ve)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    
    tree_locations: List[tuple] = response_data['tree_locations']
    polygon: Polygon =  response_data["polygon"]


    missing_coords:List[Tuple[float, float]] = missing_tree_imputer_service.impute_missing_tree_coords(
        polygon, tree_locations,orchard_id
        )

    missing_trees = [{"lat": lat, "lng": lng} for lng, lat in missing_coords]

    logger.info(f"missing trees: {missing_trees}")
    return {"missing_trees": missing_trees}

@app.get("/orchards/{orchard_id}/plot/download", summary="Download Orchard Plot Image")
async def download_orchard_plot(
    orchard_id: int = Path(..., example=216269, description="ID of orchard")
):
    """
    Returns an image of the orchard with exisiting and missing trees.
    """
    file_path = f"plots/plot_{orchard_id}.png"

    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail=f"Orchard {orchard_id}  image not found.")

    return FileResponse(
        file_path,
        media_type="image/png",
        filename=os.path.basename(file_path)
    )

