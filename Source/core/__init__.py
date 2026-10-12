"""
Package Source.core: Module cốt lõi quản lý trạng thái, luật chơi và bàn cờ Bloxorz.
"""

from core.state import Orientation, Direction, GameState, DIR_DELTAS
from core.special_tiles import TileType, SwitchType, SwitchAction, BridgeInfo, SwitchInfo
from core.transition import roll_solid_block, roll_split_cube, check_cube_merge
from core.board import BloxorzBoard

__all__ = [
    "Orientation",
    "Direction",
    "DIR_DELTAS",
    "GameState",
    "TileType",
    "SwitchType",
    "SwitchAction",
    "BridgeInfo",
    "SwitchInfo",
    "roll_solid_block",
    "roll_split_cube",
    "check_cube_merge",
    "BloxorzBoard"
]
