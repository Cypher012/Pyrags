from fastapi import APIRouter

from app.health.schemas import HealthResponse

router = APIRouter()


@router.get("/", response_model=HealthResponse)
def read_root() -> HealthResponse:
    return HealthResponse(status="ok", service="pyrags")
