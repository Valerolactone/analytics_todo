from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient


class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db_name: Optional[str] = None

    @classmethod
    async def connect(cls, mongo_uri: str, db_name: str):
        cls.client = AsyncIOMotorClient(mongo_uri)
        cls.db_name = db_name
        print("MongoDB connected.")

    @classmethod
    async def close(cls):
        if cls.client:
            cls.client.close()
            print("MongoDB disconnected.")

    @classmethod
    def get_database(cls):
        if cls.client is None or cls.db_name is None:
            raise Exception("MongoDB client not initialized.")
        return cls.client.get_database(cls.db_name)

    @classmethod
    def get_project_repository(cls):
        from database.repositories import ProjectRepository

        return ProjectRepository(cls.get_database())

    @classmethod
    def get_task_repository(cls):
        from database.repositories import TaskRepository

        return TaskRepository(cls.get_database())
