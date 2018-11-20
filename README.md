# bindr

![PyPI](https://img.shields.io/pypi/v/bindr.svg?style=flat-square) ![python](https://img.shields.io/pypi/pyversions/bindr.svg?style=flat-square) ![TravisCI](https://img.shields.io/travis/chrisrink10/bindr.svg?style=flat-square) ![Coveralls github](https://img.shields.io/coveralls/github/chrisrink10/bindr.svg?style=flat-square) ![license](https://img.shields.io/github/license/chrisrink10/bindr.svg?style=flat-square)

Bind dictionary data into named tuples and dataclasses automatically
for typed attribute access throughout the rest of your codebase.

```python
from bindr import bind
from typing import Dict, List, NamedTuple
from yaml import safe_load

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
    
config = bind(Config, safe_load("config.yaml"))
config.s3_settings.max_item_size  # <-- int
```

## Installation

Bindr is developed on [GitHub](https://github.com/chrisrink10/bindr) and 
hosted on [PyPI](https://pypi.python.org/pypi/bindr). You can fetch Bindr 
using a simple:

```bash
pip install bindr
```

## License

MIT License