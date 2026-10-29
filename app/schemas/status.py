
from pydantic import BaseModel


class ServiceStatus(BaseModel):
    name: str
    status: str
    url: str


class DashboardStatus(BaseModel):
    app: str
    status: str
    services: list[ServiceStatus]
