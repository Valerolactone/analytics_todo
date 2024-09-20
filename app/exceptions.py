class ProjectNotFoundException(Exception):
    def __init__(self, title: str):
        super().__init__(f"Project with title {title} not found.")
        self.title = title


class TaskNotFoundException(Exception):
    def __init__(self, title: str):
        super().__init__(f"Task with title {title} not found.")
        self.title = title


class ParticipantNotFoundException(Exception):
    def __init__(self, executor_id: int):
        super().__init__(f"Participant with id {executor_id} not found.")
        self.executor_id = executor_id
