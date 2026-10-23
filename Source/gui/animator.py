"""
Quản lý diễn hoạt lăn khối và playback cho GUI Bloxorz.
"""

import time
import math
from typing import List, Optional, Tuple
from core.state import GameState, Orientation


def detect_direction(from_st: GameState, to_st: GameState) -> str:
    """Tự động suy luận hướng di chuyển giữa 2 trạng thái liên tiếp."""
    if from_st.is_split and to_st.is_split:
        act_idx = from_st.active_cube
        r0, c0 = from_st.cubes[act_idx]
        r1, c1 = to_st.cubes[act_idx] if act_idx < len(to_st.cubes) else (r0, c0)
        if c1 > c0: return "RIGHT"
        if c1 < c0: return "LEFT"
        if r1 > r0: return "DOWN"
        if r1 < r0: return "UP"
        return "RIGHT"
    elif not from_st.is_split and not to_st.is_split:
        r0, c0 = from_st.pos
        r1, c1 = to_st.pos
        if c1 > c0: return "RIGHT"
        if c1 < c0: return "LEFT"
        if r1 > r0: return "DOWN"
        if r1 < r0: return "UP"
        if from_st.orientation == Orientation.STANDING and to_st.orientation == Orientation.HORIZONTAL:
            return "RIGHT"
        if from_st.orientation == Orientation.STANDING and to_st.orientation == Orientation.VERTICAL:
            return "DOWN"
        return "RIGHT"
    elif not from_st.is_split and to_st.is_split:
        return "SPLIT"
    elif from_st.is_split and not to_st.is_split:
        return "MERGE"
    return "RIGHT"


class MoveAnimation:
    """Quản lý một diễn hoạt lăn mượt mà giữa hai trạng thái."""
    def __init__(self, from_state: GameState, to_state: GameState, move_dir: str, duration: float):
        self.from_state = from_state
        self.to_state = to_state
        self.move_dir = move_dir
        self.duration = max(0.04, duration)
        self.start_time = time.time()
        self.progress = 0.0
        self.is_finished = False

    def update(self) -> float:
        """Cập nhật tiến trình lăn (0.0 -> 1.0) với hàm làm mượt Cosine Ease-In-Out."""
        elapsed = time.time() - self.start_time
        if elapsed >= self.duration:
            self.progress = 1.0
            self.is_finished = True
            return 1.0
        t = elapsed / self.duration
        self.progress = 0.5 * (1.0 - math.cos(math.pi * t))
        return self.progress


class FallingAnimation:
    """Diễn hoạt khối lăn ra ngoài rồi rơi khỏi bàn cờ."""
    def __init__(self, from_state, to_state, move_dir: str, duration: float = 0.85):
        self.duration = max(0.1, duration)
        self.from_state = from_state
        self.to_state = to_state
        self.move_dir = move_dir
        self.start_time = time.time()
        self.progress = 0.0
        self.is_finished = False
        self.roll_progress = 0.0
        self.fall_progress = 0.0

    def update(self) -> float:
        elapsed = time.time() - self.start_time
        if elapsed >= self.duration:
            self.progress = 1.0
            self.roll_progress = 1.0
            self.fall_progress = 1.0
            self.is_finished = True
            return self.progress

        t = elapsed / self.duration
        self.progress = t
        roll_end = 0.42
        if t <= roll_end:
            self.roll_progress = t / roll_end
            self.fall_progress = 0.0
        else:
            self.roll_progress = 1.0
            self.fall_progress = ((t - roll_end) / (1.0 - roll_end)) ** 2
        return self.progress


class PlaybackAnimator:
    """Bộ điều khiển diễn hoạt đường đi giải đố."""
    def __init__(self):
        self.is_playing = False
        self.current_step = 0
        self.speed = 1.0
        self.speeds = [1.0, 2.0, 4.0, 0.5]
        self.active_animation: Optional[MoveAnimation] = None
        self.pause_timer: float = 0.0

    def reset(self):
        """Khởi động lại trình phát về bước ban đầu."""
        self.is_playing = False
        self.current_step = 0
        self.active_animation = None
        self.pause_timer = 0.0

    def toggle_play(self):
        """Chuyển đổi trạng thái Play / Pause."""
        self.is_playing = not self.is_playing
        if not self.is_playing:
            self.active_animation = None

    def cycle_speed(self) -> float:
        """Chuyển đổi vòng lặp tốc độ phát lại."""
        curr_idx = self.speeds.index(self.speed) if self.speed in self.speeds else 0
        self.speed = self.speeds[(curr_idx + 1) % len(self.speeds)]
        return self.speed

    def step_forward(self, max_steps: int) -> int:
        """Tiến tới một bước."""
        self.is_playing = False
        self.active_animation = None
        if self.current_step < max_steps - 1:
            self.current_step += 1
        return self.current_step

    def step_backward(self) -> int:
        """Lùi lại một bước."""
        self.is_playing = False
        self.active_animation = None
        if self.current_step > 0:
            self.current_step -= 1
        return self.current_step

    def update(
        self,
        states_path: List[GameState],
        actions_path: Optional[List[str]] = None
    ) -> Tuple[Optional[GameState], Optional[MoveAnimation]]:
        """Cập nhật khung hình diễn hoạt."""
        if not self.is_playing or not states_path:
            return None, None

        curr_time = time.time()

        if self.active_animation is not None:
            self.active_animation.update()
            if self.active_animation.is_finished:
                self.current_step += 1
                completed_state = self.active_animation.to_state
                self.active_animation = None
                self.pause_timer = curr_time + (0.05 / self.speed)
                return completed_state, None
            return None, self.active_animation

        if curr_time < self.pause_timer:
            return None, None

        if self.current_step < len(states_path) - 1:
            from_st = states_path[self.current_step]
            to_st = states_path[self.current_step + 1]
            act = (
                actions_path[self.current_step]
                if actions_path and self.current_step < len(actions_path)
                else detect_direction(from_st, to_st)
            )
            duration = max(0.06, 0.22 / self.speed)
            self.active_animation = MoveAnimation(from_st, to_st, act, duration)
            return None, self.active_animation
        else:
            self.is_playing = False
            return None, None
