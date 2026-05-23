import asyncio
import json
import time

import flet as ft


class SwipeHandlersMixin:
    def _extract_local_delta(self, e, axis: str) -> float:
        local_delta = getattr(e, "local_delta", None)
        if local_delta is not None:
            value = getattr(local_delta, axis, None)
            if value is not None:
                try:
                    return float(value)
                except Exception:
                    pass

        direct_keys = {
            "x": ("delta_x", "dx", "primary_delta"),
            "y": ("delta_y", "dy"),
        }
        for key in direct_keys.get(axis, ()):
            value = getattr(e, key, None)
            if value is None:
                continue
            try:
                return float(value)
            except Exception:
                pass

        raw_data = getattr(e, "data", None)
        if isinstance(raw_data, str):
            try:
                payload = json.loads(raw_data)
            except Exception:
                payload = None
            if isinstance(payload, dict):
                for key in direct_keys.get(axis, ()):
                    value = payload.get(key)
                    if value is None:
                        continue
                    try:
                        return float(value)
                    except Exception:
                        pass
                compound = payload.get("local_delta") or payload.get("delta")
                if isinstance(compound, dict):
                    value = compound.get(axis)
                    if value is not None:
                        try:
                            return float(value)
                        except Exception:
                            pass

        return 0.0

    def _extract_delta_x(self, e) -> float:
        return self._extract_local_delta(e, "x")

    def _extract_delta_y(self, e) -> float:
        return self._extract_local_delta(e, "y")

    def _set_card_motion_animation(self, animation):
        if self.card is None:
            return

        self.card.animate_position = animation
        self.card.animate_rotation = animation
        self.card.animate_opacity = animation

    def _use_live_drag_animation(self):
        self._set_card_motion_animation(getattr(self, "drag_live_animation", None))

    def _use_settle_drag_animation(self):
        self._set_card_motion_animation(getattr(self, "card_drag_animation", None))

    def _start_drag_session(self, _):
        self.is_dragging = True
        self.drag_dx = 0.0
        self.drag_target_dx = 0.0
        self.drag_raw_dx = 0.0
        self.drag_velocity_x = 0.0
        self.drag_last_render_dx = 0.0
        self.last_drag_direction = 0
        self.last_pan_event = time.perf_counter()

        if self.card is not None:
            self._use_live_drag_animation()
            self.card.left = self.card_base_left
            self.card.top = self.card_base_top
            self.card.rotate = 0
            self.card.opacity = 1
            if getattr(self, "card_idle_shadow", None) is not None:
                self.card.shadow = []
            try:
                self.card.update()
            except Exception:
                pass

    def on_pan_start(self, e):
        if self.current_view != "round" or self.round_state is None or self.in_transition:
            return
        self._start_drag_session(e)

    def on_pan_update(self, e):
        if self.current_view != "round" or self.round_state is None or self.in_transition:
            return
        if not self.is_dragging:
            self._start_drag_session(e)

        now = time.perf_counter()
        dt_event = now - self.last_pan_event if self.last_pan_event > 0 else 1 / 60
        dt_event = self._clamp(dt_event, 1 / 240, 0.08)
        self.last_pan_event = now

        dx = self._extract_delta_x(e)
        dy = self._extract_delta_y(e)

        dx = self._clamp(dx, -28.0, 28.0)
        dy = self._clamp(dy, -12.0, 12.0)

        next_left = self._clamp(
            float(self.card.left or self.card_base_left) + dx,
            self.card_base_left - self.swipe_max_dx,
            self.card_base_left + self.swipe_max_dx,
        )
        next_top = self._clamp(
            float(self.card.top or self.card_base_top) + dy * 0.18,
            self.card_base_top - 28.0,
            self.card_base_top + 28.0,
        )

        self.drag_dx = next_left - self.card_base_left
        self.drag_target_dx = self.drag_dx
        self.drag_raw_dx = self.drag_dx
        self.drag_velocity_x = self.drag_velocity_x * 0.62 + (dx / dt_event) * 0.38

        self._render_drag_frame(next_left, next_top, self.drag_dx)

    def _render_drag_frame(self, left: float, top: float, drag_dx: float):
        if (
            self.current_view != "round"
            or self.round_state is None
            or self.card is None
            or self.left_hint is None
            or self.right_hint is None
        ):
            return

        if abs(drag_dx - self.drag_last_render_dx) < 0.2:
            return

        self.drag_last_render_dx = drag_dx
        drag_ratio = self._clamp(drag_dx / max(1.0, self.swipe_max_dx), -1.0, 1.0)

        self.card.left = left
        self.card.top = top
        self.card.rotate = drag_ratio * 0.22
        self.card.opacity = max(0.3, 1 - abs(drag_dx) / (self.swipe_max_dx * 1.7))

        hint_opacity = self._clamp((abs(drag_dx) - 18.0) / 72.0, 0.0, 1.0)
        if drag_dx > 0:
            self.right_hint.opacity = hint_opacity
            self.left_hint.opacity = 0.0
            self._set_state_tint(self._theme()["ok"], hint_opacity * 0.14, update_now=False)
        elif drag_dx < 0:
            self.left_hint.opacity = hint_opacity
            self.right_hint.opacity = 0.0
            self._set_state_tint(self._theme()["bad"], hint_opacity * 0.14, update_now=False)
        else:
            self.left_hint.opacity = 0.0
            self.right_hint.opacity = 0.0
            self._set_state_tint(self._theme()["accent"], 0.0, update_now=False)

        try:
            self.card.update()
            self.left_hint.update()
            self.right_hint.update()
            if self.state_tint is not None:
                self.state_tint.update()
        except Exception:
            pass

    def on_pan_end(self, _):
        if self.current_view != "round" or self.round_state is None or self.in_transition:
            return

        self.is_dragging = False
        if self.card is not None and getattr(self, "card_idle_shadow", None) is not None:
            self.card.shadow = self.card_idle_shadow

        decision_dx = float(self.card.left or self.card_base_left) - self.card_base_left
        meaningful_drag = abs(decision_dx) >= 24.0
        fast_flick = meaningful_drag and abs(self.drag_velocity_x) >= 620.0
        if abs(decision_dx) >= self.swipe_commit_threshold or fast_flick:
            direction_ok = decision_dx > 0 if abs(decision_dx) >= 8 else self.drag_velocity_x > 0
            self.page.run_task(self._commit_swipe, direction_ok)
        else:
            self.reset_position()

    def _manual_swipe(self, is_correct: bool):
        if self.current_view != "round" or self.round_state is None or self.in_transition:
            return
        self.is_dragging = False
        self._use_settle_drag_animation()
        self.page.run_task(self._commit_swipe, is_correct)

    async def _commit_swipe(self, is_correct: bool):
        if self.current_view != "round" or self.round_state is None or self.in_transition:
            return

        self.in_transition = True
        try:
            self.is_dragging = False
            self._use_settle_drag_animation()
            theme = self._theme()
            direction = 1 if is_correct else -1
            color = theme["ok"] if is_correct else theme["bad"]

            if self.card is not None:
                self.card.left = self.card_base_left + (self.swipe_max_dx + 420) * direction
                self.card.top = self.card_base_top
                self.card.rotate = 0.34 * direction
                self.card.opacity = 0.0
            self.left_hint.opacity = 1.0 if not is_correct else 0.0
            self.right_hint.opacity = 1.0 if is_correct else 0.0
            self._set_state_tint(color, 0.28)
            if not self._safe_update(self.card, self.left_hint, self.right_hint, self.state_tint):
                return

            await asyncio.sleep(self._anim_ms(190) / 1000)
            if self.current_view != "round" or self.round_state is None:
                return
            if not self._page_is_active():
                return

            self._register_answer(is_correct)
            self._next_word()
            self._update_round_hud()
            self._reset_card_visuals()
            self._safe_update()
        finally:
            self.in_transition = False

    def reset_position(self):
        self._reset_card_visuals()
        self._safe_update(self.card, self.left_hint, self.right_hint, self.state_tint)

    def _reset_card_visuals(self):
        self.is_dragging = False
        if self.card is not None:
            self._use_settle_drag_animation()
            self.card.left = self.card_base_left
            self.card.top = self.card_base_top
            self.card.rotate = 0
            self.card.opacity = 1
            if getattr(self, "card_idle_shadow", None) is not None:
                self.card.shadow = self.card_idle_shadow
        if self.left_hint is not None:
            self.left_hint.opacity = 0
        if self.right_hint is not None:
            self.right_hint.opacity = 0
        self.drag_dx = 0.0
        self.drag_target_dx = 0.0
        self.drag_raw_dx = 0.0
        self.drag_velocity_x = 0.0
        self.drag_last_render_dx = 0.0
        self.last_pan_event = 0.0
        self.last_drag_direction = 0
        self._set_state_tint(self._theme()["accent"], 0.0)
