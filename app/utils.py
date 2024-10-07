from enum import Enum


class TaskStatus(Enum):
    OPEN = "open"
    IN_PROGRESS = "in progress"
    RESOLVED = "resolved"
    REOPENED = "reopened"
    CLOSED = "closed"
