import asyncio
import json
import logging

from aiokafka import AIOKafkaConsumer

from database.session import MongoDB
from settings import settings

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("kafka_consumer.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


class KafkaConsumer:
    def __init__(
        self, topic: str, group_id: str, broker: str = settings.kafka_bootstrap_servers
    ):
        self.topic = topic
        self.group_id = group_id
        self.consumer = AIOKafkaConsumer(
            self.topic,
            loop=asyncio.get_event_loop(),
            bootstrap_servers=broker,
            group_id=self.group_id,
            auto_offset_reset="earliest",
        )
        self.project_repo = MongoDB.get_project_repository()
        self.task_repo = MongoDB.get_task_repository()

    async def start(self):
        await self.consumer.start()
        try:
            await self.consume_messages()
        finally:
            await self.consumer.stop()

    async def consume_messages(self):
        try:
            async for message in self.consumer:
                await self.process_message(message)
        except Exception as e:
            logger.error(f"Error while consuming messages: {e}", exc_info=True)
        finally:
            await self.consumer.stop()

    async def process_message(self, message):
        try:
            decoded_message = json.loads(message.value().decode("utf-8"))
            key = decoded_message.get("key")

            if key == "create_project":
                await self.project_repo.create_project(
                    title=decoded_message.get("title"),
                    participant_id=decoded_message.get("participant_id"),
                )
            elif key == "update_project":
                await self.project_repo.update_project_active_status(
                    title=decoded_message.get("title"),
                    is_active=decoded_message.get("is_active"),
                )
            elif key == "create_task":
                task_id = await self.task_repo.create_task(
                    title=decoded_message.get("title"),
                    project_title=decoded_message.get("project_title"),
                    status=decoded_message.get("status"),
                    executor_id=decoded_message.get("executor_id"),
                )

                await self.project_repo.update_project_tasks_and_participants_lists(
                    title=decoded_message.get("project_title"),
                    task=task_id,
                    participants_ids=[
                        decoded_message.get("executor_id"),
                        decoded_message.get("assigner_id"),
                    ],
                )
            elif key == "update_task":
                if decoded_message.get("is_active"):
                    await self.task_repo.update_task_active_status(
                        title=decoded_message.get("title"),
                        is_active=decoded_message.get("is_active"),
                    )

                elif decoded_message.get("executor_id") and decoded_message.get(
                    "executor_name"
                ):
                    await self.task_repo.update_task_executor(
                        title=decoded_message.get("title"),
                        executor_id=decoded_message.get("executor_id"),
                    )

                    await self.project_repo.update_project_participants_lists(
                        title=decoded_message.get("project_title"),
                        participants_ids=[
                            decoded_message.get("executor_id"),
                            decoded_message.get("assigner_id"),
                        ],
                    )

                elif decoded_message.get("status"):
                    await self.task_repo.update_task_status(
                        title=decoded_message.get("title"),
                        status=decoded_message.get("status"),
                    )

        except Exception as e:
            logger.error(f"Error while processing message: {e}", exc_info=True)
