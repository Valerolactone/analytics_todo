from fastapi import APIRouter, HTTPException, Path, status

from app.exceptions import ParticipantNotFoundException, ProjectNotFoundException
from app.schemas import ParticipantStatistics, ProjectStatistics, Statistics
from app.services import StatisticsService

statistics_router = APIRouter()


@statistics_router.get("/", response_model=Statistics, status_code=status.HTTP_200_OK)
async def read_statistics():
    statistics_service = StatisticsService()
    return await statistics_service.get_statistics()


@statistics_router.get(
    "/{project_title}", response_model=ProjectStatistics, status_code=status.HTTP_200_OK
)
async def read_project_statistics(project_title: str = Path(...)):
    try:
        statistics_service = StatisticsService()
        return await statistics_service.get_project_statistics(project_title)
    except ProjectNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@statistics_router.get(
    "/weekly/{executor_id}",
    response_model=ParticipantStatistics,
    status_code=status.HTTP_200_OK,
)
async def read_participant_statistics(executor_id: int = Path(...)):
    try:
        statistics_service = StatisticsService()
        return await statistics_service.get_weekly_participant_statistics(executor_id)
    except ParticipantNotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
