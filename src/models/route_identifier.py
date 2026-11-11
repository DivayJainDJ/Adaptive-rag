"""
Route identifier model.
"""

from typing import Literal

from pydantic import BaseModel, Field


class RouteIdentifier(BaseModel):
    """Model for routing queries to appropriate nodes."""

    route: Literal["index", "general", "search"] = Field(
        description="index if the retrieved context can answer the question, general for common knowledge, search for live/external facts"
    )
