from pydantic import BaseModel


class SessionCreateRequest(BaseModel):
    source_page: str | None = None


class SessionCreateResponse(BaseModel):
    session_token: str
