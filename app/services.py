from app.schemas import ParticipantStatistics, ProjectStatistics, Statistics
from database.session import MongoDB


class StatisticsService:
    def __init__(self):
        self.project_repo = MongoDB.get_project_repository()
        self.task_repo = MongoDB.get_task_repository()

    async def get_statistics(self) -> Statistics:
        total_projects = await self.project_repo.count_projects()
        total_tasks = await self.task_repo.count_tasks()
        total_participants = await self.project_repo.count_unique_participants()

        return Statistics(
            total_projects=total_projects,
            total_tasks=total_tasks,
            total_participants=total_participants,
        )

    async def get_project_statistics(self, title: str) -> ProjectStatistics:
        project = await self.project_repo.get_project_by_title(title)
        project_id = await project["project_id"]
        project_participants = await self.project_repo.get_project_participants(
            project_id
        )
        total_tasks = await self.task_repo.count_tasks_for_project(project_id)
        status_percentages = await self.task_repo.get_task_status_counts(project_id)
        avg_completion_time = await self.task_repo.get_average_completion_time(
            project_id
        )

        return ProjectStatistics(
            project_id=project_id,
            title=project["title"],
            total_participants=project_participants,
            total_tasks=total_tasks,
            avg_completion_time_in_hours=avg_completion_time,
            status_percentages=status_percentages,
        )

    async def get_weekly_participant_statistics(
        self, participant_id: int
    ) -> ParticipantStatistics:
        projects_stats = await self.task_repo.get_weekly_participant_stats(
            participant_id
        )

        return ParticipantStatistics(
            participant_id=participant_id,
            projects_statistics=projects_stats,
        )
