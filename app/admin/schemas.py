from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel


@dataclass(frozen=True)
class EventListResponse:
    items: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class EventDetailResponse:
    template: dict[str, Any]
    options: list[dict[str, Any]] = field(default_factory=list)


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class AdminSessionResponse(BaseModel):
    authenticated: bool = True
    username: str
