from __future__ import annotations

from typing import NamedTuple, List, Dict, Optional
from dataclasses import dataclass


class PEP563ConfigNamedTuple(NamedTuple):
    class SMSServiceConfig(NamedTuple):
        host: str
        port: int
        username: str
        password: str

    class S3Config(NamedTuple):
        default_bucket: str
        default_region: str
        max_item_size: int

    class InvalidConfig(NamedTuple):
        support_emails: List[str]

    class Unspecialized(NamedTuple):
        support_emails: List

    support_emails: List[str]
    api_key: str
    timeout_ms: int
    pi: float
    sms_providers: List[PEP563ConfigNamedTuple.SMSServiceConfig]
    s3_settings: PEP563ConfigNamedTuple.S3Config
    accounts: Dict[str, str]
    backup_db_hostname: Optional[str]
    db_region: Optional[str]
    db_credentials: tuple
    no_reply_email: str = "no-reply@python.org"


@dataclass
class PEP563ConfigDataclass:
    @dataclass
    class SMSServiceConfig:
        host: str
        port: int
        username: str
        password: str

    @dataclass
    class S3Config:
        default_bucket: str
        default_region: str
        max_item_size: int

    @dataclass
    class InvalidConfig:
        support_emails: List[str]

    @dataclass
    class Unspecialized:
        support_emails: List

    support_emails: List[str]
    api_key: str
    timeout_ms: int
    pi: float
    sms_providers: List[PEP563ConfigDataclass.SMSServiceConfig]
    s3_settings: PEP563ConfigDataclass.S3Config
    accounts: Dict[str, str]
    backup_db_hostname: Optional[str]
    db_region: Optional[str]
    db_credentials: tuple
    no_reply_email: str = "no-reply@python.org"
