from __future__ import annotations

from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

STATUS_COLORS = {
    "active": "green",
    "expired": "red",
    "frozen": "orange",
    "paused": "orange",
    "booked": "blue",
    "attended": "green",
    "cancelled": "red",
    "no plan": "gray",
}
STATUS_ICONS = {
    "active": ":material/check_circle:",
    "expired": ":material/event_busy:",
    "frozen": ":material/ac_unit:",
    "paused": ":material/pause_circle:",
    "booked": ":material/event_available:",
    "attended": ":material/how_to_reg:",
    "cancelled": ":material/cancel:",
    "no plan": ":material/info:",
}
ROLE_ICONS = {
    "admin": ":material/admin_panel_settings:",
    "trainer": ":material/sports:",
    "member": ":material/person:",
}
FLASH_ICONS = {
    "success": ":material/check_circle:",
    "error": ":material/error:",
    "warning": ":material/warning:",
}


def asset(name: str) -> str:
    return str(ASSETS / name)


def inject_css() -> None:
    css_path = ASSETS / "style.css"
    if css_path.exists():
        st.html(f"<style>{css_path.read_text(encoding='utf-8')}</style>")


def show_brand() -> None:
    icon = ASSETS / "pulse-logo.png"
    if icon.exists():
        st.logo(str(icon))
    else:
        wordmark = ASSETS / "logo.svg"
        if wordmark.exists():
            st.logo(str(wordmark))


def page_header(title: str, caption: str = "", icon: str = ":material/exercise:") -> None:
    st.header(f"{icon} {title}")
    if caption:
        st.caption(caption)


def show_image(filename: str, *, width: str | int = "stretch") -> bool:
    path = ASSETS / filename
    if not path.exists():
        return False
    st.image(str(path), width=width)
    return True


def hero(filename: str = "hero-floor.png") -> None:
    show_image(filename)


def class_art(name: str) -> str | None:
    text = name.lower()
    if any(word in text for word in ("yoga", "stretch", "flow", "mobility")):
        file_name = "class-yoga.png"
    elif any(word in text for word in ("spin", "cycle", "bike")):
        file_name = "class-cycle.png"
    elif any(word in text for word in ("abs", "core")):
        file_name = "class-core.png"
    elif any(word in text for word in ("strength", "lift", "circuit")):
        file_name = "class-strength.png"
    else:
        file_name = "class-hiit.png"
    path = ASSETS / file_name
    return str(path) if path.exists() else None


def show_class_art(name: str) -> None:
    path = class_art(name)
    if path:
        st.image(path, width="stretch")


def class_icon(name: str) -> str:
    text = name.lower()
    if any(word in text for word in ("yoga", "stretch", "flow", "mobility")):
        return ":material/self_improvement:"
    if any(word in text for word in ("spin", "cycle", "bike")):
        return ":material/directions_bike:"
    if any(word in text for word in ("abs", "core")):
        return ":material/accessibility_new:"
    if any(word in text for word in ("strength", "lift", "circuit")):
        return ":material/fitness_center:"
    return ":material/bolt:"


def flash() -> None:
    message = st.session_state.pop("flash", None)
    kind = st.session_state.pop("flash_kind", "success")
    if not message:
        return
    icon = FLASH_ICONS.get(kind, ":material/info:")
    if kind == "error":
        st.error(message, icon=icon)
    elif kind == "warning":
        st.warning(message, icon=icon)
    else:
        st.success(message, icon=icon)


def set_flash(message: str, kind: str = "success") -> None:
    st.session_state.flash = message
    st.session_state.flash_kind = kind


def status_badge(status: str | None) -> None:
    label = (status or "no plan").replace("_", " ")
    key = label.lower()
    st.badge(
        label.title(),
        icon=STATUS_ICONS.get(key, ":material/info:"),
        color=STATUS_COLORS.get(key, "gray"),
    )


def empty(message: str, icon: str = ":material/inbox:") -> None:
    with st.container(border=True):
        st.markdown(f"### {icon}")
        st.caption(message)


def inr(amount: float) -> str:
    return f"₹{amount:,.0f}"


def initials(name: str) -> str:
    parts = [part for part in name.split() if part]
    if not parts:
        return "?"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[-1][0]).upper()


def person_title(name: str, role: str | None = None) -> None:
    icon = ROLE_ICONS.get(role or "member", ":material/person:")
    st.markdown(f"{icon} **{name}**")


def render_self_checkin(
    user_id: int,
    allowed: bool,
    reason: str,
    key_prefix: str,
    *,
    show_block_reason: bool = True,
) -> None:
    from services.attendance import check_in, check_in_time, todays_check_in

    visit = todays_check_in(user_id)
    if visit:
        st.success(
            f"Checked in at {check_in_time(visit)}.",
            icon=":material/check_circle:",
        )
        return
    if not allowed:
        if show_block_reason and reason:
            st.warning(reason, icon=":material/warning:")
        st.button(
            "Check in",
            type="primary",
            disabled=True,
            icon=":material/block:",
            key=f"{key_prefix}_disabled",
        )
        return
    confirm_key = f"{key_prefix}_confirm"
    if st.session_state.get(confirm_key):
        st.warning("Confirm you are at the gym now?", icon=":material/warning:")
        yes, no = st.columns(2)
        if yes.button("Yes, I am here", type="primary", key=f"{key_prefix}_yes", icon=":material/how_to_reg:"):
            st.session_state.pop(confirm_key, None)
            ok, message = check_in(user_id, source="self")
            set_flash(message, "success" if ok else "error")
            st.rerun()
        if no.button("Not now", key=f"{key_prefix}_no", icon=":material/close:"):
            st.session_state.pop(confirm_key, None)
            st.rerun()
    elif st.button("Check in", type="primary", key=f"{key_prefix}_start", icon=":material/login:"):
        st.session_state[confirm_key] = True
        st.rerun()


def membership_panel(membership: dict, member_name: str | None = None) -> None:
    with st.container(border=True):
        photo, body = st.columns([1, 2.2], vertical_alignment="center")
        with photo:
            hero("hero-floor.png")
        with body:
            st.subheader(f":material/card_membership: {membership['plan_name']}")
            status_badge(membership["status"])
            if member_name:
                st.caption(member_name)
            st.markdown(
                f"{membership['start_date']} → {membership['end_date']}  \n"
                f"**{inr(membership['plan_price'])}** · {membership['duration_days']} days"
            )
