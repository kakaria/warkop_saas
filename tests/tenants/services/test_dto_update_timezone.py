import pytest

from tenants.dto import UpdateTimezoneDTO


@pytest.mark.parametrize(
    "invalid_timezone, expected_error",
    [
        ("hahaha", ValueError),
        ("Asia/Pasific", ValueError),
    ],
)
def test_update_timezone_dto_rejects_invalid_timezone(
    invalid_timezone,
    expected_error,
):
    # langsung Act
    with pytest.raises(expected_error) as exc_info:
        UpdateTimezoneDTO(timezone=invalid_timezone)

    assert "tidak valid" in str(exc_info.value).lower()
