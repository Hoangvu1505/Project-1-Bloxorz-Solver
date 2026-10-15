"""
Định nghĩa GameState và Orientation cho Bloxorz.
"""

from enum import Enum, IntEnum
from typing import Tuple, Optional, List, Any


class Orientation(IntEnum):
    STANDING = 0
    HORIZONTAL = 1
    VERTICAL = 2


class Direction(str, Enum):
    UP = "UP"
    DOWN = "DOWN"
    LEFT = "LEFT"
    RIGHT = "RIGHT"


DIR_DELTAS = {
    Direction.UP: (-1, 0),
    Direction.DOWN: (1, 0),
    Direction.LEFT: (0, -1),
    Direction.RIGHT: (0, 1),
}


class GameState:
    """Biểu diễn trạng thái của khối và cầu trên bàn cờ."""
    __slots__ = ('is_split', 'orientation', 'pos', 'cubes', 'active_cube', 'bridge_states', '_hash')

    def __init__(
        self,
        is_split: bool,
        orientation: Optional[Orientation],
        pos: Optional[Tuple[int, int]],
        cubes: Optional[Tuple[Tuple[int, int], Tuple[int, int]]],
        active_cube: int,
        bridge_states: Tuple[bool, ...]
    ):
        self.is_split = is_split
        self.bridge_states = tuple(bridge_states)

        if not is_split:
            self.orientation = orientation
            self.pos = pos
            self.cubes = None
            self.active_cube = 0
            self._hash = hash((False, orientation, pos, self.bridge_states))
        else:
            c0, c1 = cubes
            if c0 > c1:                      # hoán đổi thì phải đảo active_cube
                c0, c1 = c1, c0
                active_cube = 1 - active_cube
            self.orientation = None
            self.pos = None
            self.cubes = (c0, c1)
            self.active_cube = active_cube
            self._hash = hash((True, self.cubes, active_cube, self.bridge_states))

    def __hash__(self) -> int:
        return self._hash

    def __eq__(self, other: Any) -> bool:
        if self is other:
            return True
        if not isinstance(other, GameState) or self._hash != other._hash:
            return False
        if self.is_split != other.is_split or self.bridge_states != other.bridge_states:
            return False
        if not self.is_split:
            return self.orientation == other.orientation and self.pos == other.pos
        return self.cubes == other.cubes and self.active_cube == other.active_cube

    def __repr__(self) -> str:
        if not self.is_split:
            return f"GameState({self.orientation.name}, pos={self.pos}, bridges={self.bridge_states})"
        return (f"GameState(SPLIT, cubes={self.cubes}, active={self.active_cube}, "
                f"bridges={self.bridge_states})")

    def get_occupied_cells(self) -> List[Tuple[int, int]]:
        if self.is_split:
            return list(self.cubes)
        r, c = self.pos
        if self.orientation == Orientation.STANDING:
            return [(r, c)]
        if self.orientation == Orientation.HORIZONTAL:
            return [(r, c), (r, c + 1)]
        return [(r, c), (r + 1, c)]          # VERTICAL

    def get_active_cube_pos(self) -> Optional[Tuple[int, int]]:
        if self.is_split:
            return self.cubes[self.active_cube]
        return None

    def clone_with_active_cube(self, active_cube: int) -> 'GameState':
        if not self.is_split:
            return self
        return GameState(True, None, None, self.cubes, active_cube, self.bridge_states)

