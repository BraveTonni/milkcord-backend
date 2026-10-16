from pydantic import BaseModel, ConfigDict
from datetime import datetime


class CallStartRequest(BaseModel):
    to_user_id: int
    kind: str  # audio | video | screen


class CallEndRequest(BaseModel):
    call_id: int


class CallAcceptRequest(BaseModel):
    call_id: int


class CallRejectRequest(BaseModel):
    call_id: int


class CallModel(BaseModel):
    id: int
    caller_id: int
    callee_id: int
    kind: str
    started_at: datetime
    ended_at: datetime | None = None
    closed_by: int | None = None

    model_config = ConfigDict(from_attributes=True)


class CallResponse(BaseModel):
    call: CallModel
