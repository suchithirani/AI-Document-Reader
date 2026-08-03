from app.common.base_schema import BaseSchema


class HealthResponse(BaseSchema):
    status: str
    application: str
    version: str