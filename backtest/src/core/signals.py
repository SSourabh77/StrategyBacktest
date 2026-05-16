from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class SignalType(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"
    EXIT = "EXIT"
    HOLD = "HOLD"


@dataclass(frozen=True)
class Signal:
    datetime: datetime
    signal: SignalType
    strength: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def normalize_signal(value: str | SignalType) -> SignalType:
    if isinstance(value, SignalType):
        return value
    return SignalType(str(value).upper())

