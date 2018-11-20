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
    }


class TestNamedTuple:
    @pytest.fixture(scope="class")
    def Config(self):
        class Config(NamedTuple):
            class SMSServiceConfig(NamedTuple):
                host: str
                port: int
                username: str
                password: str

            class S3Config(NamedTuple):
                default_bucket: str
                default_region: str
                max_item_size: int

            support_emails: List[str]
            api_key: str
            timeout_ms: int
            pi: float
            sms_providers: List[SMSServiceConfig]
            s3_settings: S3Config
            accounts: Dict[str, str]
            backup_db_hostname: Optional[str]
            no_reply_email: str = "no-reply@python.org"

        return Config

    def test_bind_named_tuple(
        self, Config, config_dict, s3_settings_dict, sms_providers
    ):
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
        ) == bind(Config, config_dict)

    def test_forbid_unspecialized_generic(self):
        class InvalidConfig(NamedTuple):
            support_emails: List

        with pytest.raises(TypeError):
            bind(InvalidConfig, {"support_emails": ["something"]})

    def test_raise_on_missing_attr(self):
        class InvalidConfig(NamedTuple):
            support_emails: List[str]

        with pytest.raises(AttributeError):
            bind(InvalidConfig, {"support_emails": ["something"], "api_key": "abcd"})

    def test_allow_missing_attr(self):
        class InvalidConfig(NamedTuple):
            support_emails: List[str]

        assert InvalidConfig(["something"]) == bind(
            InvalidConfig,
            {"support_emails": ["something"], "api_key": "abcd"},
            raise_if_missing_attr=False,
        )


try:
    from dataclasses import dataclass
except ImportError:
    pass


@pytest.mark.skipif(sys.version_info < (3, 7), reason="dataclass added in Python 3.7")
class TestDataClass:
    @pytest.fixture
    def ConfigDataClass(self):
        @dataclass
        class Config:
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

            support_emails: List[str]
            api_key: str
            timeout_ms: int
            pi: float
            sms_providers: List[SMSServiceConfig]
            s3_settings: S3Config
            accounts: Dict[str, str]
            backup_db_hostname: Optional[str]
            no_reply_email: str = "no-reply@python.org"

        return Config

    def test_bind_dataclass(
        self, ConfigDataClass, config_dict, s3_settings_dict, sms_providers
    ):
        assert ConfigDataClass(
            config_dict["support_emails"],
            config_dict["api-key"],
            config_dict["timeout ms"],
            config_dict["pi"],
            [
                ConfigDataClass.SMSServiceConfig(
                    sms_providers[0]["host"],
                    sms_providers[0]["port"],
                    sms_providers[0]["username"],
                    sms_providers[0]["password"],
                )
            ],
            ConfigDataClass.S3Config(
                s3_settings_dict["default_bucket"],
                s3_settings_dict["default_region"],
                s3_settings_dict["max_item_size"],
            ),
            config_dict["accounts"],
            config_dict["backup_db_hostname"],
        ) == bind(ConfigDataClass, config_dict)

    def test_forbid_unspecialized_generic(self):
        @dataclass
        class InvalidConfig:
            support_emails: List

        with pytest.raises(TypeError):
            bind(InvalidConfig, {"support_emails": ["something"]})

    def test_raise_on_missing_attr(self):
        @dataclass
        class InvalidConfig:
            support_emails: List[str]

        with pytest.raises(AttributeError):
            bind(InvalidConfig, {"support_emails": ["something"], "api_key": "abcd"})

    def test_allow_missing_attr(self):
        @dataclass
        class InvalidConfig:
            support_emails: List[str]

        assert InvalidConfig(["something"]) == bind(
            InvalidConfig,
            {"support_emails": ["something"], "api_key": "abcd"},
            raise_if_missing_attr=False,
        )
