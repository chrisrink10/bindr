import __future__

import sys
from typing import NamedTuple, List, Dict, Optional

import pytest

from bindr import bind


@pytest.fixture
def sms_providers():
    return [
        {
            "host": "api.twilio.com",
            "port": 443,
            "username": "twilio",
            "password": "password",
        }
    ]


@pytest.fixture
def s3_settings_dict():
    return {
        "default_bucket": "company-bucket",
        "default_region": "us-east-1",
        "max_item_size": 2048,
    }


@pytest.fixture
def config_dict(s3_settings_dict, sms_providers):
    return {
        "api-key": "abcd",
        "timeout ms": 3875,
        "pi": 3.14,
        "support_emails": ["crink@crink.com", "crink@bindr.readthedocs.io"],
        "s3_settings": s3_settings_dict,
        "sms_providers": sms_providers,
        "accounts": {"crink": "password", "crink2": "securepw"},
        "backup_db_hostname": None,
        "db-region": "us-east-1",
        "db-credentials": ("admin", "password1"),
    }


try:
    from ._pep563_config import PEP563ConfigNamedTuple, PEP563ConfigDataclass
except (ImportError, SyntaxError):
    PEP563ConfigNamedTuple = None
    PEP563ConfigDataclass = None


class ConfigNamedTuple(NamedTuple):
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
    sms_providers: List[SMSServiceConfig]
    s3_settings: S3Config
    accounts: Dict[str, str]
    backup_db_hostname: Optional[str]
    db_region: Optional[str]
    db_credentials: tuple
    no_reply_email: str = "no-reply@python.org"


try:
    from dataclasses import dataclass
except ImportError:

    def dataclass(v):
        return v


@dataclass
class ConfigDataclass:
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
    sms_providers: List[SMSServiceConfig]
    s3_settings: S3Config
    accounts: Dict[str, str]
    backup_db_hostname: Optional[str]
    db_region: Optional[str]
    db_credentials: tuple
    no_reply_email: str = "no-reply@python.org"


@pytest.fixture(
    params=[
        ConfigNamedTuple,
        pytest.param(
            PEP563ConfigNamedTuple,
            marks=pytest.mark.skipif(
                not hasattr(__future__, "annotations"),
                reason="no __future__.annotations support",
            ),
        ),
        pytest.param(
            ConfigDataclass,
            marks=pytest.mark.skipif(
                sys.version_info < (3, 7), reason="dataclass added in Python 3.7"
            ),
        ),
        pytest.param(
            PEP563ConfigDataclass,
            marks=pytest.mark.skipif(
                sys.version_info < (3, 7), reason="dataclass added in Python 3.7"
            ),
        ),
    ]
)
def Config(request):
    return request.param


def test_bind_named_tuple(Config, config_dict, s3_settings_dict, sms_providers):
    assert Config(
        config_dict["support_emails"],
        config_dict["api-key"],
        config_dict["timeout ms"],
        config_dict["pi"],
        [
            Config.SMSServiceConfig(
                sms_providers[0]["host"],
                sms_providers[0]["port"],
                sms_providers[0]["username"],
                sms_providers[0]["password"],
            )
        ],
        Config.S3Config(
            s3_settings_dict["default_bucket"],
            s3_settings_dict["default_region"],
            s3_settings_dict["max_item_size"],
        ),
        config_dict["accounts"],
        config_dict["backup_db_hostname"],
        config_dict["db-region"],
        config_dict["db-credentials"],
    ) == bind(Config, config_dict)


def test_forbid_unspecialized_generic(Config):
    with pytest.raises(TypeError):
        bind(Config.Unspecialized, {"support_emails": ["something"]})


def test_raise_on_missing_attr(Config):
    with pytest.raises(AttributeError):
        bind(Config.InvalidConfig, {"support_emails": ["something"], "api_key": "abcd"})


def test_allow_missing_attr(Config):
    assert Config.InvalidConfig(["something"]) == bind(
        Config.InvalidConfig,
        {"support_emails": ["something"], "api_key": "abcd"},
        raise_if_missing_attr=False,
    )
