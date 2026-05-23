import unittest

from ui.swipe_handlers import SwipeHandlersMixin


class FakeControl:
    def __init__(self):
        self.left = 0.0
        self.top = 0.0
        self.rotate = 0.0
        self.opacity = 1.0
        self.shadow = ["idle"]
        self.animate_position = None
        self.animate_rotation = None
        self.animate_opacity = None

    def update(self):
        pass


class SwipeHarness(SwipeHandlersMixin):
    def __init__(self):
        self.current_view = "round"
        self.round_state = object()
        self.in_transition = False
        self.is_dragging = False
        self.drag_dx = 0.0
        self.drag_target_dx = 0.0
        self.drag_raw_dx = 0.0
        self.drag_velocity_x = 0.0
        self.drag_last_render_dx = 0.0
        self.last_drag_direction = 0
        self.last_pan_event = 0.0
        self.card_base_left = 10.0
        self.card_base_top = 8.0
        self.swipe_max_dx = 260.0
        self.swipe_commit_threshold = 92.0
        self.card_drag_animation = "settle-animation"
        self.drag_live_animation = "live-drag-animation"
        self.card_idle_shadow = ["idle"]
        self.card = FakeControl()
        self.left_hint = FakeControl()
        self.right_hint = FakeControl()
        self.state_tint = FakeControl()
        self.updated_controls = []

    def _clamp(self, value, min_value, max_value):
        return max(min_value, min(max_value, value))

    def _theme(self):
        return {"accent": "accent", "ok": "ok", "bad": "bad"}

    def _set_state_tint(self, *_, **__):
        pass

    def _safe_update(self, *controls):
        self.updated_controls.append(controls)
        return True


class SwipeAnimationTests(unittest.TestCase):
    def test_drag_session_uses_live_animation(self):
        app = SwipeHarness()
        app.card.animate_position = app.card_drag_animation
        app.card.animate_rotation = app.card_drag_animation
        app.card.animate_opacity = app.card_drag_animation

        app._start_drag_session(None)

        self.assertIs(app.card.animate_position, app.drag_live_animation)
        self.assertIs(app.card.animate_rotation, app.drag_live_animation)
        self.assertIs(app.card.animate_opacity, app.drag_live_animation)

    def test_reset_position_restores_settle_animation(self):
        app = SwipeHarness()
        app.card.animate_position = app.drag_live_animation
        app.card.animate_rotation = app.drag_live_animation
        app.card.animate_opacity = app.drag_live_animation

        app.reset_position()

        self.assertIs(app.card.animate_position, app.card_drag_animation)
        self.assertIs(app.card.animate_rotation, app.card_drag_animation)
        self.assertIs(app.card.animate_opacity, app.card_drag_animation)

    def test_fast_flick_needs_meaningful_drag_distance(self):
        app = SwipeHarness()
        app.drag_velocity_x = 900.0
        app.card.left = app.card_base_left + 5.0
        app.reset_position_called = False

        def mark_reset():
            app.reset_position_called = True

        app.reset_position = mark_reset

        app.on_pan_end(None)

        self.assertTrue(app.reset_position_called)


if __name__ == "__main__":
    unittest.main()
