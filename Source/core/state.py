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

    #hàm cần code lại
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
        self.orientation = orientation
        self.pos = pos

        if cubes is not None:
            c0, c1 = cubes
            self.cubes = (c0, c1) if c0 <= c1 else (c1, c0)
        else:
            self.cubes = None

        self.active_cube = active_cube
        self.bridge_states = tuple(bridge_states)

        if not self.is_split:
            self._hash = hash((False, self.orientation, self.pos, self.bridge_states))
        else:
            self._hash = hash((True, self.cubes, self.active_cube, self.bridge_states))

    #hàm cần code lại
    def __hash__(self) -> int:
        return self._hash

    #hàm cần code lại
    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, GameState):
            return False
        if self.is_split != other.is_split or self.bridge_states != other.bridge_states:
            return False
        if not self.is_split:
            return self.orientation == other.orientation and self.pos == other.pos
        else:
            return self.cubes == other.cubes and self.active_cube == other.active_cube

    #hàm cần code lại
    def get_occupied_cells(self) -> List[Tuple[int, int]]:
        """Trả về danh sách toạ độ (r, c) các ô mà khối đang chiếm giữ."""
        if not self.is_split:
            r, c = self.pos
            if self.orientation == Orientation.STANDING:
                return [(r, c)]
            elif self.orientation == Orientation.HORIZONTAL:
                return [(r, c), (r, c + 1)]
            elif self.orientation == Orientation.VERTICAL:
                return [(r, c), (r + 1, c)]
        else:
            return [self.cubes[0], self.cubes[1]]
        return []

    #hàm cần code lại
    def get_active_cube_pos(self) -> Optional[Tuple[int, int]]:
        """Trả về toạ độ khối con đang điều khiển khi split."""
        if self.is_split and self.cubes:
            return self.cubes[self.active_cube]
        return None

    #hàm cần code lại
    def clone_with_active_cube(self, active_cube: int) -> 'GameState':
        """Tạo bản sao trạng thái với khối con active mới."""
        return GameState(
            is_split=self.is_split,
            orientation=self.orientation,
            pos=self.pos,
            cubes=self.cubes,
            active_cube=active_cube,
            bridge_states=self.bridge_states
        )

