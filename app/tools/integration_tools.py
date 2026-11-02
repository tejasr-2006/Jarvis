"""Trusted handlers for the standalone Email and Fitness Manager services."""
from app.integrations.email_manager import EmailManagerClient
from app.integrations.fitness_manager import FitnessManagerClient


_email_client = EmailManagerClient()
_fitness_client = FitnessManagerClient()


async def read_high_priority_emails() -> list | dict:
    return await _email_client.get_high_priority_emails()


async def read_workouts() -> list:
    return await _fitness_client.get_workouts()
