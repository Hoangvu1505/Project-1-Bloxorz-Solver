"""
Định nghĩa các loại ô đặc biệt, cầu và công tắc trong Bloxorz.
"""

from enum import Enum, IntEnum
from typing import List, Tuple, Dict, Optional, Any


class TileType(IntEnum):
    VOID = 0
    FLOOR = 1
    GOAL = 2
    FRAGILE = 3
    BRIDGE = 4


class SwitchType(str, Enum):
    SOFT = "soft"
    HEAVY = "heavy"
    SPLIT = "split"


class SwitchAction(str, Enum):
    TOGGLE = "toggle"
    PERMANENT = "permanent"


class BridgeInfo:
    """Thông tin về cầu nối trong màn chơi."""
    def __init__(self, bridge_id: int, tiles: List[Tuple[int, int]], initial_open: bool = False):
        self.bridge_id = bridge_id
        self.tiles = [tuple(t) for t in tiles]
        self.initial_open = initial_open

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.bridge_id,
            "tiles": self.tiles,
            "initial_open": self.initial_open
        }


class SwitchInfo:
    """Thông tin về công tắc trên bàn cờ."""
    def __init__(
        self,
        pos: Tuple[int, int],
        switch_type: SwitchType,
        action: SwitchAction = SwitchAction.TOGGLE,
        bridge_ids: Optional[List[int]] = None,
        split_targets: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None
    ):
        self.pos = tuple(pos)
        self.switch_type = SwitchType(switch_type)
        self.action = SwitchAction(action)
        self.bridge_ids = bridge_ids or []
        self.split_targets = tuple(split_targets) if split_targets else None

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "pos": list(self.pos),
            "type": self.switch_type.value,
            "action": self.action.value,
            "bridge_ids": self.bridge_ids
        }
        if self.split_targets:
            data["split_targets"] = [list(self.split_targets[0]), list(self.split_targets[1])]
        return data

