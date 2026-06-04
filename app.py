import hashlib
from datetime import datetime, timezone

import pandas as pd
import requests
import streamlit as st


# =========================
# Internal (fixed in code)
# =========================
PROJECT_ID = "mot-saudi"
TAXONOMY_ID = "default"
SKIP_STEPS = {}

API_URL = "https://public-api.anecdoteai.com/inject"
BRAND_COLOR = "#0E1115"
DEFAULT_SOURCE = "demo"


# =========================
# Color helpers (derive all shades from BRAND_COLOR)
# =========================
def _hex_to_rgb(hex_color: str):
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def _mix(hex_color: str, target, ratio: float) -> str:
    r, g, b = _hex_to_rgb(hex_color)
    tr, tg, tb = target
    return "#{:02x}{:02x}{:02x}".format(
        round(r + (tr - r) * ratio),
        round(g + (tg - g) * ratio),
        round(b + (tb - b) * ratio),
    )


_R, _G, _B = _hex_to_rgb(BRAND_COLOR)
BRAND_HOVER = _mix(BRAND_COLOR, (255, 255, 255), 0.18)  # lighter on hover (visible feedback)
BRAND_BG = _mix(BRAND_COLOR, (255, 255, 255), 0.96)     # very light tint for panels
BRAND_BORDER = f"rgba({_R}, {_G}, {_B}, 0.20)"


# =========================
# Styling (brand look)
# =========================
def inject_brand_style():
    st.markdown(
        f"""
        <style>
          :root {{
            --brand: {BRAND_COLOR};
            --brand-hover: {BRAND_HOVER};
            --brand-bg: {BRAND_BG};
            --brand-border: {BRAND_BORDER};
          }}

          .block-container {{
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 860px;
          }}

          .brand-hero {{
            background: var(--brand-bg);
            border: 1px solid var(--brand-border);
            border-left: 8px solid var(--brand);
            border-radius: 18px;
            padding: 16px 18px;
            margin-bottom: 12px;
          }}

          .brand-title {{
            font-size: 26px;
            font-weight: 800;
            margin: 0;
            color: var(--brand);
          }}

          .brand-subtitle {{
            margin-top: 4px;
            font-size: 13px;
            color: rgba(14, 17, 21, 0.70);
          }}

          div[data-testid="stButton"] > button {{
            background: var(--brand);
            border: 1px solid var(--brand);
            color: white;
            border-radius: 12px;
            padding: 0.6rem 1rem;
            font-weight: 700;
          }}

          div[data-testid="stButton"] > button:hover {{
            background: var(--brand-hover);
            border-color: var(--brand-hover);
          }}

          div[data-testid="stForm"] {{
            border: 1px solid var(--brand-border);
            border-radius: 18px;
            padding: 14px 16px;
            background: white;
          }}

          a {{
            color: var(--brand) !important;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================
# Helpers
# =========================
def get_api_headers():
    token = st.secrets.get("ANECDOTE_API_TOKEN", "").strip()
    if not token:
        return None
    return {"Authorization": f"Bearer {token}"}


def make_reference_id(message: str) -> str:
    digest = hashlib.sha256(message.strip().encode("utf-8")).hexdigest()[:16]
    return f"msg-{digest}"


def now_iso_utc() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_payload(message: str, source: str, filters: dict) -> dict:
    reference_id = make_reference_id(message)

    return {
        "project_id": PROJECT_ID,
        "taxonomy_id": TAXONOMY_ID,
        "skip_steps": SKIP_STEPS,
        "batch": [
            {
                "message": message,
                "ds": now_iso_utc(),
                "unique_id": reference_id,
                "ticket_id": reference_id,
                "source": source,
                "filters": filters,
            }
        ],
    }


def send_to_api(payload: dict):
    headers = get_api_headers()

    if not API_URL.strip():
        return False, None, "API_URL is not set. Sending is disabled."

    if not headers:
        return (
            False,
            None,
            "Missing ANECDOTE_API_TOKEN in Streamlit secrets. Add it before submitting.",
        )

    try:
        resp = requests.post(
            API_URL.strip(),
            json=payload,
            headers=headers,
            timeout=30,
        )
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        return resp.ok, resp.status_code, body
    except requests.exceptions.RequestException as e:
        return False, None, str(e)


# =========================
# UI
# =========================
st.set_page_config(page_title="MOT Saudi Demo Submission", layout="centered")
inject_brand_style()

st.markdown(
    """
    <div class="brand-hero">
      <div class="brand-title">MOT Saudi Demo Submission</div>
      <div class="brand-subtitle">Submit a message for the MOT Saudi demo project.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(f"Submissions will be sent to: **{PROJECT_ID}**")

with st.form("submission_form"):
    st.subheader("Required details")
    message = st.text_area("Message *", placeholder="Type the message here...")

    source_value = DEFAULT_SOURCE
    filters_dict = {}

    with st.expander("Optional details (click to expand)", expanded=False):
        source_input = st.text_input(
            "Data source (optional)",
            placeholder=f'Defaults to "{DEFAULT_SOURCE}"',
            help=f'Where did this message come from? If left blank, it will be set to "{DEFAULT_SOURCE}".',
        )
        source_value = source_input.strip() if source_input.strip() else DEFAULT_SOURCE

        st.markdown("**Extra attributes (optional)**")
        st.caption("Add any extra details as key/value pairs (example: platform = iOS).")

        default_rows = pd.DataFrame([{"Attribute": "", "Value": ""} for _ in range(3)])
        edited = st.data_editor(
            default_rows,
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
        )

        for _, row in edited.iterrows():
            key = str(row.get("Attribute", "")).strip()
            if key:
                value = row.get("Value", "")
                filters_dict[key] = "" if value is None else str(value)

    submitted = st.form_submit_button("Create submission")

if submitted:
    if not message.strip():
        st.error("Message is required.")
        st.stop()

    payload = build_payload(
        message=message.strip(),
        source=source_value,
        filters=filters_dict if isinstance(filters_dict, dict) else {},
    )

    st.success("Submission created.")
    with st.expander("View technical preview (optional)", expanded=False):
        st.json(payload)

    ok, status, body = send_to_api(payload)

    if status is None and not ok:
        st.error(body)
    else:
        st.write(f"Result: **{status}**")
        if ok:
            st.success("Sent successfully.")
        else:
            st.error("Sending failed.")
        with st.expander("Response details", expanded=False):
            if isinstance(body, (dict, list)):
                st.json(body)
            else:
                st.text(str(body))
