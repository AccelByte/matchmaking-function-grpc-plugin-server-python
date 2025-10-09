from dataclasses import dataclass
from typing import Optional


class ValidationError(Exception):
    pass


@dataclass
class AllianceRule:
    min_number: int = 0
    max_number: int = 0
    player_min_number: int = 0
    player_max_number: int = 0


@dataclass
class GameRules:
    shipCountMin: int = 0
    shipCountMax: int = 0
    auto_backfill: bool = False
    alliance: Optional[AllianceRule] = None

    def validate(self) -> None:
        if not self.alliance:
            raise ValidationError("alliance rule missing")
        if self.alliance.min_number > self.alliance.max_number:
            raise ValidationError("alliance rule MaxNumber is less than MinNumber")
        if self.alliance.player_min_number > self.alliance.player_max_number:
            raise ValidationError("alliance rule PlayerMaxNumber is less than PlayerMinNumber")
        if self.shipCountMin > self.shipCountMax:
            raise ValidationError("ShipCountMax is less than ShipCountMin")
