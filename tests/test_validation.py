from pathlib import Path

import pytest

from lnkup.core.models import LnkSpec, PayloadType
from lnkup.core.validation import validate_spec


def test_ntlm_spec(tmp_path: Path):
    validate_spec(LnkSpec(host="192.0.2.10", output=tmp_path / "a.lnk"))


def test_environment_requires_variables(tmp_path: Path):
    with pytest.raises(ValueError):
        validate_spec(
            LnkSpec(
                host="192.0.2.10",
                output=tmp_path / "a.lnk",
                payload_type=PayloadType.ENVIRONMENT,
            )
        )
