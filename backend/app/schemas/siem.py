from datetime import datetime
from typing import Literal
from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field, model_validator
from app.models.siem_connection import SiemProvider

class SiemConnectRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    provider: SiemProvider
    base_url: AnyHttpUrl
    token: str | None = Field(default=None, min_length=1, max_length=4096)
    username: str | None = Field(default=None, min_length=1, max_length=256)
    password: str | None = Field(default=None, min_length=1, max_length=4096)
    index_name: str | None = Field(default=None, max_length=256)
    verify_ssl: bool = True
    @model_validator(mode="after")
    def credentials_required(self):
        if self.provider == SiemProvider.splunk and not self.token: raise ValueError("Splunk requires an API token")
        if self.provider == SiemProvider.wazuh and not (self.username and self.password): raise ValueError("Wazuh requires username and password")
        return self

class SiemConnectionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str; provider: SiemProvider; base_url: str; index_name: str | None
    verify_ssl: bool; enabled: bool; connected: bool; last_error: str | None
    last_checked_at: datetime | None; last_synced_at: datetime | None

class SiemTestOut(BaseModel):
    provider: SiemProvider; connected: bool; message: str

class SiemSyncOut(BaseModel):
    provider: SiemProvider; fetched: int; created: int; duplicates: int; failed: int; synced_at: datetime

class DashboardKpiOut(BaseModel):
    connection_status: Literal["connected", "disconnected", "not_configured"]
    provider: SiemProvider | None; last_synced_at: datetime | None
    total_alerts: int; critical_alerts: int; high_alerts: int; active_incidents: int; contained_threats: int
