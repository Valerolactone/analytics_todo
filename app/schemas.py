from datetime import datetime
from typing import Dict, List, Optional

from bson import ObjectId
from pydantic import BaseModel, ConfigDict, validator


class TunedModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value):
        if not ObjectId.is_valid(value):
            raise ValueError("Invalid objectid")
        return ObjectId(value)

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, **kwargs):
        return {"type": "string"}


class TaskModel(BaseModel):
    task_id: PyObjectId
    project_id: PyObjectId
    title: str
    status: str
    is_active: bool
    executor_id: int
    executor_name: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    @validator("status")
    def validate_status(cls, value):
        valid_statuses = {"open", "in progress", "resolved", "reopened", "closed"}
        if value not in valid_statuses:
            raise ValueError(
                f"Invalid status: {value}. Valid statuses are {valid_statuses}."
            )
        return value


class ProjectModel(BaseModel):
    project_id: PyObjectId
    title: str
    is_active: bool
    tasks: List[PyObjectId]
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


class ParticipantStatistics(TunedModel):
    participant_id: int
    participant_name: str
    projects_statistics: List[Dict[str, str | int]]
