"""Pydantic response models for BHV API."""

from typing import Literal, Optional

from pydantic import BaseModel


class HeatmapDay(BaseModel):
    date: str  # "YYYY-MM-DD"
    count: int
    intensity: Literal[0, 1, 2, 3, 4]


class TopicSlice(BaseModel):
    category: str
    visits: int
    estimated_minutes: int
    percentage: float


class DomainRankEntry(BaseModel):
    domain: str
    category: str
    visit_count: int
    estimated_minutes: int


class ProductivityPoint(BaseModel):
    hour: int  # 0-23
    focus_minutes: int  # work + research + devtools
    distraction_minutes: int  # social + entertainment
    ratio: float


class RabbitHoleNode(BaseModel):
    id: str
    domain: str
    title: str
    category: str


class RabbitHoleSession(BaseModel):
    session_id: str
    start_time: int  # Unix timestamp
    duration_minutes: int
    visit_count: int
    dominant_topic: str
    nodes: list[RabbitHoleNode]
    edges: list[tuple[str, str]]


class DetectedBrowser(BaseModel):
    name: str
    path: str
    visit_count: int
    detected: bool
    manual_override: bool


class AppStatus(BaseModel):
    browsers: list[DetectedBrowser]
    total_visits: int
    date_range_available: tuple[str, str]  # ("YYYY-MM-DD", "YYYY-MM-DD")
    last_refreshed: Optional[int]  # Unix timestamp


class AllDatasets(BaseModel):
    status: AppStatus
    heatmap: list[HeatmapDay]
    topics: list[TopicSlice]
    domains: list[DomainRankEntry]
    productivity: list[ProductivityPoint]
    rabbit_holes: list[RabbitHoleSession]


class CategoryOverride(BaseModel):
    category: str


class BrowserPathOverride(BaseModel):
    browser: str
    path: str
