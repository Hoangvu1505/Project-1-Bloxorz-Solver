"""
Quản lý bàn cờ Bloxorz, kiểm tra va chạm, thắng thua, công tắc và sinh successor.
"""

import json
import os
from typing import List, Tuple, Dict, Optional, Any

from core.state import GameState, Orientation, Direction
from core.special_tiles import TileType, SwitchType, SwitchAction, BridgeInfo, SwitchInfo
from core.transition import roll_solid_block, roll_split_cube, check_cube_merge


class BloxorzBoard:
    """Quản lý bản đồ, luật chơi và chuyển đổi trạng thái của Bloxorz."""

    def __init__(
        self,
        name: str,
        grid: List[List[int]],
        start_pos: Tuple[int, int],
        goal_pos: Tuple[int, int],
        bridges: Optional[List[BridgeInfo]] = None,
        switches: Optional[List[SwitchInfo]] = None
    ):
        self.name = name
        self.grid = grid
        self.rows = len(grid)
        self.cols = len(grid[0]) if self.rows > 0 else 0
        self.start_pos = tuple(start_pos)
        self.goal_pos = tuple(goal_pos)

        self.bridges: Dict[int, BridgeInfo] = {}
        self.bridge_list_ids: List[int] = []
        if bridges:
            for b in bridges:
                self.bridges[b.bridge_id] = b
                self.bridge_list_ids.append(b.bridge_id)
        self.bridge_list_ids.sort()

        self.tile_to_bridge_id: Dict[Tuple[int, int], int] = {}
        for b_id, b_info in self.bridges.items():
            for tile in b_info.tiles:
                self.tile_to_bridge_id[tile] = b_id

        self.switches: Dict[Tuple[int, int], SwitchInfo] = {}
        if switches:
            for s in switches:
                self.switches[s.pos] = s

    def get_initial_state(self) -> GameState:
        """Khởi tạo trạng thái ban đầu."""
        initial_bridge_states = tuple(
            self.bridges[b_id].initial_open for b_id in self.bridge_list_ids
        )
        return GameState(
            is_split=False,
            orientation=Orientation.STANDING,
            pos=self.start_pos,
            cubes=None,
            active_cube=0,
            bridge_states=initial_bridge_states
        )

    def is_bridge_open(self, bridge_id: int, bridge_states: Tuple[bool, ...]) -> bool:
        """Kiểm tra cầu có mở không."""
        try:
            idx = self.bridge_list_ids.index(bridge_id)
            return bridge_states[idx]
        except ValueError:
            return False

    #hàm cần code lại
    def is_valid_cell(self, r: int, c: int, bridge_states: Tuple[bool, ...]) -> bool:
        """Kiểm tra toạ độ (r, c) có phải là bề mặt hợp lệ có thể bước lên hay không."""
        if r < 0 or r >= self.rows or c < 0 or c >= self.cols:
            return False
        tile = self.grid[r][c]
        if tile == TileType.VOID:
            return False
        if tile == TileType.BRIDGE:
            b_id = self.tile_to_bridge_id.get((r, c))
            if b_id is None or not self.is_bridge_open(b_id, bridge_states):
                return False
        return True

    #hàm cần code lại
    def is_state_valid(self, state: GameState) -> bool:
        """Kiểm tra trạng thái khối có hợp lệ (không bị rơi) không."""
        cells = state.get_occupied_cells()
        for r, c in cells:
            if not self.is_valid_cell(r, c, state.bridge_states):
                return False

        if not state.is_split:
            if state.orientation == Orientation.STANDING:
                r, c = state.pos
                if self.grid[r][c] == TileType.FRAGILE:
                    return False
        else:
            for r, c in state.cubes:
                if self.grid[r][c] == TileType.FRAGILE:
                    return False
        return True

    #hàm cần code lại
    def is_goal_state(self, state: GameState) -> bool:
        """Kiểm tra khối đã đứng thẳng vào ô đích hay chưa."""
        if state.is_split:
            return False
        return state.orientation == Orientation.STANDING and state.pos == self.goal_pos

    #hàm cần code lại
    def _trigger_switches(
        self,
        occupied_cells: List[Tuple[int, int]],
        is_standing: bool,
        is_split: bool,
        current_bridge_states: Tuple[bool, ...]
    ) -> Tuple[Tuple[bool, ...], Optional[Tuple[Tuple[int, int], Tuple[int, int]]]]:
        """Xử lý kích hoạt công tắc khi khối lăn tới ô mới."""
        bridge_states_dict = {
            b_id: self.is_bridge_open(b_id, current_bridge_states)
            for b_id in self.bridge_list_ids
        }
        split_triggered_targets = None

        for cell in occupied_cells:
            if cell in self.switches:
                sw = self.switches[cell]

                if sw.switch_type == SwitchType.SOFT:
                    self._apply_switch_effect(sw, bridge_states_dict)
                elif sw.switch_type == SwitchType.HEAVY:
                    if is_standing and not is_split:
                        self._apply_switch_effect(sw, bridge_states_dict)
                elif sw.switch_type == SwitchType.SPLIT:
                    if is_standing and not is_split:
                        self._apply_switch_effect(sw, bridge_states_dict)
                        split_triggered_targets = sw.split_targets

        new_bridge_states = tuple(
            bridge_states_dict[b_id] for b_id in self.bridge_list_ids
        )
        return new_bridge_states, split_triggered_targets

    #hàm cần code lại
    def _apply_switch_effect(self, sw: SwitchInfo, bridge_dict: Dict[int, bool]) -> None:
        """Thực thi tác động của công tắc lên các cầu liên kết."""
        for b_id in sw.bridge_ids:
            if b_id in bridge_dict:
                if sw.action == SwitchAction.TOGGLE:
                    bridge_dict[b_id] = not bridge_dict[b_id]
                elif sw.action == SwitchAction.PERMANENT:
                    bridge_dict[b_id] = True

    #hàm cần code lại
    def get_successors(self, state: GameState) -> List[Tuple[str, GameState, float]]:
        """Sinh tất cả các trạng thái kế tiếp hợp lệ: [(action, next_state, cost), ...]."""
        successors: List[Tuple[str, GameState, float]] = []

        if not state.is_split:
            r, c = state.pos
            ori = state.orientation

            for move in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
                new_ori, new_pos = roll_solid_block(ori, (r, c), move)

                temp_state = GameState(
                    is_split=False,
                    orientation=new_ori,
                    pos=new_pos,
                    cubes=None,
                    active_cube=0,
                    bridge_states=state.bridge_states
                )

                if self.is_state_valid(temp_state):
                    is_standing = (new_ori == Orientation.STANDING)
                    cells = temp_state.get_occupied_cells()
                    new_bridges, split_targets = self._trigger_switches(
                        cells, is_standing, is_split=False, current_bridge_states=state.bridge_states
                    )

                    step_cost = 1.0
                    for cr, cc in cells:
                        if self.grid[cr][cc] == TileType.FRAGILE:
                            step_cost += 1.0
                        if (cr, cc) in self.switches:
                            step_cost = max(0.5, step_cost - 0.2)

                    if split_targets is not None:
                        target0, target1 = split_targets
                        split_state = GameState(
                            is_split=True,
                            orientation=None,
                            pos=None,
                            cubes=(target0, target1),
                            active_cube=0,
                            bridge_states=new_bridges
                        )
                        if self.is_state_valid(split_state):
                            successors.append((f"{move.value} [SPLIT]", split_state, step_cost + 1.0))
                    else:
                        final_state = GameState(
                            is_split=False,
                            orientation=new_ori,
                            pos=new_pos,
                            cubes=None,
                            active_cube=0,
                            bridge_states=new_bridges
                        )
                        successors.append((move.value, final_state, step_cost))

        else:
            cube0, cube1 = state.cubes

            for cube_idx, (cr, cc), other_cube in [(0, cube0, cube1), (1, cube1, cube0)]:
                for move in [Direction.UP, Direction.DOWN, Direction.LEFT, Direction.RIGHT]:
                    new_c_pos = roll_split_cube((cr, cc), move)

                    if new_c_pos == other_cube:
                        continue
                    if not self.is_valid_cell(new_c_pos[0], new_c_pos[1], state.bridge_states):
                        continue
                    if self.grid[new_c_pos[0]][new_c_pos[1]] == TileType.FRAGILE:
                        continue

                    new_bridges, _ = self._trigger_switches(
                        [new_c_pos], is_standing=False, is_split=True, current_bridge_states=state.bridge_states
                    )

                    merged, merged_ori, merged_pos = check_cube_merge(new_c_pos, other_cube)
                    step_cost = 1.2
                    action_label = f"Cube{cube_idx+1}_{move.value}"

                    if merged:
                        merged_state = GameState(
                            is_split=False,
                            orientation=merged_ori,
                            pos=merged_pos,
                            cubes=None,
                            active_cube=0,
                            bridge_states=new_bridges
                        )
                        if self.is_state_valid(merged_state):
                            successors.append((f"{action_label} [MERGE]", merged_state, step_cost))
                    else:
                        new_cubes = (new_c_pos, other_cube) if cube_idx == 0 else (other_cube, new_c_pos)
                        new_split_state = GameState(
                            is_split=True,
                            orientation=None,
                            pos=None,
                            cubes=new_cubes,
                            active_cube=cube_idx,
                            bridge_states=new_bridges
                        )
                        if self.is_state_valid(new_split_state):
                            successors.append((action_label, new_split_state, step_cost))

        return successors

    def to_dict(self) -> Dict[str, Any]:
        """Chuyển bàn cờ sang dictionary."""
        return {
            "name": self.name,
            "start": list(self.start_pos),
            "goal": list(self.goal_pos),
            "grid": self.grid,
            "bridges": [b.to_dict() for b in self.bridges.values()],
            "switches": [s.to_dict() for s in self.switches.values()]
        }

    #hàm cần code lại
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'BloxorzBoard':
        """Khởi tạo bàn cờ từ dictionary JSON."""
        name = data.get("name", "Custom Stage")
        grid = data["grid"]
        start_pos = tuple(data["start"])
        goal_pos = tuple(data["goal"])

        bridges = []
        for b_data in data.get("bridges", []):
            bridges.append(BridgeInfo(
                bridge_id=b_data["id"],
                tiles=[tuple(t) for t in b_data["tiles"]],
                initial_open=b_data.get("initial_open", False)
            ))

        switches = []
        for s_data in data.get("switches", []):
            split_targets = None
            if "split_targets" in s_data and s_data["split_targets"]:
                st = s_data["split_targets"]
                split_targets = (tuple(st[0]), tuple(st[1]))

            switches.append(SwitchInfo(
                pos=tuple(s_data["pos"]),
                switch_type=SwitchType(s_data["type"]),
                action=SwitchAction(s_data.get("action", "toggle")),
                bridge_ids=s_data.get("bridge_ids", []),
                split_targets=split_targets
            ))

        return BloxorzBoard(
            name=name,
            grid=grid,
            start_pos=start_pos,
            goal_pos=goal_pos,
            bridges=bridges,
            switches=switches
        )

    #hàm cần code lại
    @staticmethod
    def load_from_file(filepath: str) -> 'BloxorzBoard':
        """Tải bàn cờ từ file JSON."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return BloxorzBoard.from_dict(data)

    def save_to_file(self, filepath: str) -> None:
        """Lưu bàn cờ vào file JSON."""
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

