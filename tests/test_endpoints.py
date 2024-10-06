from fastapi import status
from httpx import AsyncClient

from database.session import MongoDB


async def test_read_statistics(async_test_client: AsyncClient, mongo_client):
    await MongoDB.get_project_repository().create_project(
        title='Test Project', participant_id=1
    )
    await MongoDB.get_task_repository().create_task(
        project_title='Test Project', title='Test Task', status='open', executor_id=1
    )

    response = await async_test_client.get('/statistics/')

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['total_projects'] == 1
    assert data['total_tasks'] == 1
    assert data['total_participants'] == 1


async def test_read_project_statistics(async_test_client: AsyncClient, mongo_client):
    project_title = "Test Project"
    await MongoDB.get_project_repository().create_project(
        title=project_title, participant_id=1
    )
    await MongoDB.get_task_repository().create_task(
        project_title=project_title, title='Task 1', status='open', executor_id=1
    )
    await MongoDB.get_task_repository().create_task(
        project_title=project_title, title='Task 2', status='closed', executor_id=1
    )
    await MongoDB.get_task_repository().create_task(
        project_title=project_title, title='Task 3', status='in progress', executor_id=1
    )

    response = await async_test_client.get(f"/statistics/{project_title}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["title"] == project_title
    assert data["total_tasks"] == 3
    assert data["total_participants"] == 1
    assert data["status_percentages"]["open"] == 33
    assert data["status_percentages"]["closed"] == 33
    assert data["status_percentages"]["in progress"] == 33


async def test_read_project_statistics_not_found(async_test_client: AsyncClient):
    project_title = "Non-existent Project"

    response = await async_test_client.get(f"/statistics/{project_title}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == f"Project with title {project_title} not found."


async def test_read_participant_statistics(
    async_test_client: AsyncClient, mongo_client
):
    participant_id = 1
    project_title = "Test Project"
    await MongoDB.get_project_repository().create_project(project_title, participant_id)
    await MongoDB.get_task_repository().create_task(
        project_title, "Test Task", "open", participant_id
    )

    response = await async_test_client.get(f"/statistics/weekly/{participant_id}")
    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["participant_id"] == participant_id
    assert "projects_statistics" in data.keys()


async def test_read_participant_statistics_not_found(async_test_client: AsyncClient):
    executor_id = 999

    response = await async_test_client.get(f"/statistics/weekly/{executor_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == f"Participant with id {executor_id} not found."
