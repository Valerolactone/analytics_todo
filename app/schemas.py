from typing import Dict, List

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, field_validator

from app.utils import TaskStatus


class TunedModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value, field):
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid objectid")
        return ObjectId(value)


class TaskModel(BaseModel):
    title: str
    status: str
    is_active: bool
    executor_id: int
    executor_name: str

    @field_validator('status')
    def validate_status(cls, value):
        if value not in TaskStatus:
            valid_statuses = [status.value for status in TaskStatus]
            raise ValueError(
                f"Invalid status: {value}. Valid statuses are {valid_statuses}."
            )
        return value


class ProjectModel(BaseModel):
    title: str
    is_active: bool
    task: int
    participants_ids: List[int]


class Statistics(TunedModel):
    total_projects: int
    total_tasks: int
    total_participants: int


class ProjectStatistics(TunedModel):
    project_id: PyObjectId
    title: str
    total_participants: int
    total_tasks: int
    avg_completion_time_in_hours: float
    status_percentages: Dict[str, int]

    class Config:
        json_encoders = {ObjectId: str}


class ParticipantStatistics(TunedModel):
    participant_id: int
    projects_statistics: List[Dict[str, str | int]]
