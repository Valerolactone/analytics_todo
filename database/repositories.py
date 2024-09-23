from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List

from bson import ObjectId

from app.exceptions import (
    ProjectNotFoundException,
    TaskNotFoundException,
)
from app.schemas import PyObjectId


class TaskStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in progress"
    RESOLVED = "resolved"
    REOPENED = "reopened"
    CLOSED = "closed"


class ProjectRepository:
    def __init__(self, database):
        self.collection = database.get_collection("projects")

    async def count_projects(self) -> int:
        return await self.collection.count_documents({})

    async def count_unique_participants(self) -> int:
        pipeline = [
            {"$unwind": "$participants"},
            {
                "$group": {
                    "_id": None,
                    "unique_participants": {"$addToSet": "$participants"},
                }
            },
            {"$project": {"unique_participants": {"$size": "$unique_participants"}}},
        ]
        result = await self.collection.aggregate(pipeline).to_list(length=None)
        return result[0]["unique_participants"] if result else 0

    async def get_project_by_title(self, title: str) -> Dict:
        return await self.collection.find_one({"title": title})

    async def get_project_participants(self, title: str) -> int:
        project = await self.get_project_by_title(title)
        if not project:
            raise ProjectNotFoundException(title)

        total_participants = len(set(project.get("participants_ids", [])))

        return total_participants

    async def create_project(self, title: str, participant_id: int):
        new_project = {
            "title": title,
            "is_active": True,
            "tasks": [],
            "participants_ids": [
                participant_id,
            ],
            "created_at": datetime.utcnow(),
        }
        await self.collection.insert_one(new_project)

    async def update_project_active_status(self, title: str, is_active: bool):
        await self.collection.update_one(
            {"title": title}, {"$set": {"is_active": is_active}}
        )

    async def update_project_tasks_and_participants_lists(
            self, title: str, task: ObjectId, participants_ids: List[int]
    ):
        await self.collection.update_one(
            {"$title": title},
            {
                "$addToSet": {
                    "tasks": task,
                    "participants_ids": {"$each": participants_ids},
                }
            },
        )

    async def update_project_participants_lists(
            self, title: str, participants_ids: List[int]
    ):
        await self.collection.update_one(
            {"$title": title},
            {"$addToSet": {"participants_ids": {"$each": participants_ids}}},
        )


class TaskRepository:
    def __init__(self, database):
        self.collection = database.get_collection("tasks")

    async def get_task_by_title(self, title: str) -> Dict:
        return await self.collection.find_one({"title": title})

    async def count_tasks(self) -> int:
        return await self.collection.count_documents({})

    async def count_tasks_for_project(self, project_id: PyObjectId) -> int:
        return await self.collection.count_documents({"project_id": project_id})

    async def get_task_status_counts(self, project_id: PyObjectId) -> Dict[str, int]:
        pipline = [
            {"$match": {"project_id": project_id}},
            {"$group": {"_id": "$status", "$count": {"$sum": 1}}},
        ]

        result = await self.collection.aggregate(pipline).to_list(length=None)

        total_tasks = sum(item["count"] for item in result)

        status_percentages = {status.value: 0 for status in TaskStatus}

        for item in result:
            status = item["_id"]
            count = item["count"]
            percentage = (count / total_tasks * 100) if total_tasks > 0 else 0
            status_percentages[status] = percentage

        return status_percentages

    async def get_average_completion_time(self, project_id: PyObjectId) -> float:
        pipeline = [
            {"$match": {"project_id": project_id, "completed_at": {"$ne": None}}},
            {
                "$project": {
                    "completion_time": {
                        "$cond": {
                            "if": {
                                "$and": [
                                    {"$ne": ["$recompleted_at", None]},
                                    {"$ne": ["$reopened_at", None]},
                                ]
                            },
                            "then": {
                                "$add": [
                                    {"$subtract": ["$completed_at", "$created_at"]},
                                    {"$subtract": ["$recompleted_at", "$reopened_at"]},
                                ]
                            },
                            "else": {"$subtract": ["$completed_at", "$created_at"]},
                        }
                    }
                }
            },
            {
                "$group": {
                    "_id": None,
                    "average_completion_time": {"$avg": "$completion_time"},
                }
            },
        ]
        result = await self.collection.aggregate(pipeline).to_list(length=None)

        return result[0]["average_completion_time"] / (1000 * 60 * 60) if result else 0

    async def get_weekly_participant_stats(
            self, executor_id: int
    ) -> List[Dict[str, str | int]]:
        now = datetime.utcnow()
        start_of_week = now - timedelta(days=now.weekday())
        end_of_week = start_of_week + timedelta(days=7)

        start_of_week_str = start_of_week.isoformat()
        end_of_week_str = end_of_week.isoformat()

        pipeline = [
            {
                "$match": {
                    "executor_id": executor_id,
                    "completed_at": {
                        "$gte": start_of_week_str,
                        "$lte": end_of_week_str,
                    },
                }
            },
            {"$group": {"_id": "$project_id", "tasks_count": {"$sum": 1}}},
            {
                "$lookup": {
                    "from": "projects",
                    "localField": "_id",
                    "foreignField": "project_id",
                    "as": "project_info",
                }
            },
            {"$unwind": "$project_info"},
            {"$project": {"project_title": "$project_info.title", "tasks_count": 1}},
        ]

        result = await self.collection.aggregate(pipeline).to_list(length=None)

        stats = [
            {
                "project_title": item["project_title"],
                "tasks_count": item["tasks_count"],
            }
            for item in result
        ]

        return stats

    async def create_task(
            self,
            project_title: str,
            title: str,
            status: str,
            executor_id: int,
    ):
        related_project = await ProjectRepository.get_project_by_title(project_title)

        if not related_project:
            raise ProjectNotFoundException(project_title)

        project_id = related_project.get("project_id")
        new_task = {
            "project_id": project_id,
            "title": title,
            "status": status,
            "is_active": True,
            "executor_id": executor_id,
            "created_at": datetime.utcnow(),
        }
        result = await self.collection.insert_one(new_task)
        return result.inserted_id

    async def update_task_active_status(self, title: str, is_active: bool):
        await self.collection.update_one(
            {"title": title}, {"$set": {"is_active": is_active}}
        )

    async def update_task_executor(self, title: str, executor_id: int):
        await self.collection.update_one(
            {"title": title},
            {"$set": {"executor_id": executor_id}},
        )

    async def update_task_status(self, title: str, status: str):
        task = await self.get_task_by_title(title)

        if not task:
            raise TaskNotFoundException(title)

        updates = {"status": status}

        if status in [TaskStatus.RESOLVED, TaskStatus.CLOSED] and task.get("completed_at") is None:
            updates["completed_at"] = datetime.utcnow()
        if status == TaskStatus.REOPENED and task.get("completed_at") is not None:
            updates["reopened_at"] = datetime.utcnow()
        if status in [TaskStatus.RESOLVED, TaskStatus.CLOSED] and task.get("reopened_at") is not None:
            updates["recompleted_at"] = datetime.utcnow()

        await self.collection.update_one({"title": title}, {"$set": updates})
