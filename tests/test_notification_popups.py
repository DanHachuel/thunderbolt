from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MAIN_SOURCE = (ROOT / "app" / "main.py").read_text(encoding="utf-8")


def test_global_notification_toast_runs_outside_notifications_page():
    cycle_start = MAIN_SOURCE.index("def _render_notification_toast_cycle()")
    cycle_end = MAIN_SOURCE.index("def localized_tab_labels", cycle_start)
    cycle_source = MAIN_SOURCE[cycle_start:cycle_end]
    main_start = MAIN_SOURCE.index("def main():")
    main_source = MAIN_SOURCE[main_start:]

    assert "reconcile_persisted_notifications()" in cycle_source
    assert "list_notifications(limit=500, unread_only=True)" in cycle_source
    assert "NOTIFICATION_TOAST_SEEN_KEY" in MAIN_SOURCE
    assert "NOTIFICATION_TOAST_INITIALISED_KEY" in MAIN_SOURCE
    assert "st.toast(body)" in cycle_source
    assert "pending[:NOTIFICATION_TOAST_MAX_PER_CYCLE]" in cycle_source
    assert '@st.fragment(run_every=NOTIFICATION_TOAST_INTERVAL)' in cycle_source
    assert "render_global_notification_toasts()" in main_source
    assert main_source.index("render_global_notification_toasts()") < main_source.index("renderers.get(current_page")


def test_global_notification_toast_is_positioned_at_bottom_right():
    css_start = MAIN_SOURCE.index("/* Notificações globais:")
    css_end = MAIN_SOURCE.index("</style>", css_start)
    css = MAIN_SOURCE[css_start:css_end]

    assert '[data-testid="stToastContainer"]' in css
    assert "bottom:1rem" in css
    assert "right:1rem" in css
    assert "top:auto" in css
    assert "z-index:100000" in css


def test_notification_toast_keeps_history_read_state_unchanged():
    cycle_start = MAIN_SOURCE.index("def _render_notification_toast_cycle()")
    cycle_end = MAIN_SOURCE.index("def localized_tab_labels", cycle_start)
    cycle_source = MAIN_SOURCE[cycle_start:cycle_end]

    assert "mark_notification_read" not in cycle_source
    assert "mark_all_notifications_read" not in cycle_source
    assert "unread_only=True" in cycle_source
