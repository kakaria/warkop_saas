from dataclasses import dataclass
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError



@dataclass(frozen=True)
class UpdateTimezoneDTO:
    timezone: str

    def __post_init__(self):
        try:
            ZoneInfo(self.timezone)
        except ZoneInfoNotFoundError:
            raise ValueError("Timezone tidak valid!")

