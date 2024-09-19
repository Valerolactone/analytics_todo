from datetime import datetime, timedelta
from typing import Any, Dict, List

from app.exceptions import ParticipantNotFoundException, ProjectNotFoundException
from app.schemas import PyObjectId


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


class TaskRepository:
    def __init__(self, database):
        self.collection = database.get_collection("tasks")

    async def count_tasks(self) -> int:
        return await self.collection.count_documents({})

    async def count_tasks_for_project(self, project_id: PyObjectId) -> int:
        return await self.collection.count_documents({"project_id": project_id})

    async def get_task_status_counts(self, project_id: PyObjectId) -> Dict[str, int]:
        possible_statuses = ["open", "in progress", "resolved", "reopened", "closed"]

        pipline = [
            {"$match": {"project_id": project_id}},
            {"$group": {"_id": "$status", "$count": {"$sum": 1}}},
        ]

        result = await self.collection.aggregate(pipline).to_list(length=None)

        total_tasks = sum(item["count"] for item in result)

        status_percentages = {status: 0 for status in possible_statuses}

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
                    "completion_time": {"$subtract": ["$completed_at", "$created_at"]}
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

    async def get_executor_name_from_execution_id(self, execution_id: int) -> str:
        document = await self.collection.find_one(
            {"execution_id": execution_id}, projection={"executor_name": 1, "_id": 0}
        )
        if document is None:
            raise ParticipantNotFoundException(execution_id)
        return document["executor_name"]

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
