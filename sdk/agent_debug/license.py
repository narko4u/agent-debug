"""
AgentDebug Licensing — trial counter, license verification, and watermark.

Implements the D+F+E model:
  D — 50-use trial with countdown notices (40 → 30 → ... → 1)
  F — Export features and advanced tools locked without license
  E — Watermark overlay on HTML dashboard output
"""

import json
import os
import sys
import shutil
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────────

_LICENSE_DIR = Path.home() / ".agent_debug"
_COUNTER_FILE = _LICENSE_DIR / "trial_counter.json"
_LICENSE_FILE = _LICENSE_DIR / "license.key"

TRIAL_LIMIT = 50
COUNTDOWN_START = 40
PURCHASE_URL = "https://empirelabs1.gumroad.com/l/agent-debug"
LICENSE_PRICE = "$95"


# ── Exceptions ─────────────────────────────────────────────────────

class LicenseError(Exception):
    """Raised when trial is expired or feature requires license."""
    pass


# ── Counter / License helpers ──────────────────────────────────────

def _ensure_dir():
    _LICENSE_DIR.mkdir(parents=True, exist_ok=True)


def _load_counter() -> dict:
    """Load the trial counter. Returns {'uses': 0, 'notified': []} if missing."""
    _ensure_dir()
    if not _COUNTER_FILE.exists():
        return {"uses": 0, "notified": [], "last_check": None}
    try:
        return json.loads(_COUNTER_FILE.read_text())
    except (json.JSONDecodeError, IOError):
        return {"uses": 0, "notified": [], "last_check": None}


def _save_counter(data: dict):
    _ensure_dir()
    _COUNTER_FILE.write_text(json.dumps(data, indent=2))


def is_licensed() -> bool:
    """Check if a valid license file exists."""
    if not _LICENSE_FILE.exists():
        return False
    try:
        data = json.loads(_LICENSE_FILE.read_text())
        return data.get("licensed", False) is True
    except (json.JSONDecodeError, IOError):
        return False


def activate_license(key: str) -> bool:
    """Activate AgentDebug with a license key from Gumroad.
    
    Args:
        key: The license key string.
    
    Returns:
        True if activation succeeded.
    
    Note:
        In a full implementation this would verify against Gumroad's
        License API. For now, any non-empty key activates.
    """
    if not key or not key.strip():
        return False
    
    _ensure_dir()
    data = {
        "licensed": True,
        "key": key.strip(),
        "activated_at": datetime.now(timezone.utc).isoformat(),
    }
    _LICENSE_FILE.write_text(json.dumps(data, indent=2))
    
    # Remove trial counter — no longer needed
    if _COUNTER_FILE.exists():
        _COUNTER_FILE.unlink()
    
    return True


def deactivate_license():
    """Remove the license file (reset to trial)."""
    if _LICENSE_FILE.exists():
        _LICENSE_FILE.unlink()


# ── Trial check (D) ────────────────────────────────────────────────

def check_trial() -> dict:
    """Check trial status. Returns dict with:
        - allowed: bool — whether tracing is permitted
        - remaining: int — remaining trial uses
        - message: str — notification message (empty if all good)
        - licensed: bool
    """
    if is_licensed():
        return {"allowed": True, "remaining": -1, "message": "", "licensed": True}
    
    counter = _load_counter()
    used = counter.get("uses", 0)
    remaining = max(0, TRIAL_LIMIT - used)
    
    if used >= TRIAL_LIMIT:
        return {
            "allowed": False,
            "remaining": 0,
            "message": (
                f"🚫 AgentDebug trial expired ({TRIAL_LIMIT} uses used).\n"
                f"Purchase the full SDK at {PURCHASE_URL} for {LICENSE_PRICE} (one-time, forever)."
            ),
            "licensed": False,
        }
    
    # Countdown notices (D)
    notified = counter.get("notified", [])
    message = ""
    
    if remaining <= 10 and remaining > 0:
        # Final 10 — every use gets a warning
        if remaining not in notified:
            notified.append(remaining)
            _save_counter({**counter, "notified": notified})
        message = (
            f"⚠️  AgentDebug trial: {remaining} uses remaining.\n"
            f"Purchase at {PURCHASE_URL} for {LICENSE_PRICE} to unlock unlimited use."
        )
    elif used >= COUNTDOWN_START and remaining not in notified:
        # First countdown notice at 40
        notified.append(remaining)
        _save_counter({**counter, "notified": notified})
        message = (
            f"📊 AgentDebug trial: {remaining} uses remaining.\n"
            f"After {TRIAL_LIMIT} uses, tracing will require a license ({PURCHASE_URL})."
        )
    
    return {
        "allowed": True,
        "remaining": remaining,
        "message": message,
        "licensed": False,
    }


def increment_usage():
    """Record one trial use and save updated counter."""
    if is_licensed():
        return
    counter = _load_counter()
    counter["uses"] = counter.get("uses", 0) + 1
    counter["last_check"] = datetime.now(timezone.utc).isoformat()
    _save_counter(counter)


def assert_tracing_allowed():
    """Raise LicenseError if trial is exhausted. Called by @trace and TraceInspector."""
    status = check_trial()
    if not status["allowed"]:
        raise LicenseError(status["message"])
    if status["message"]:
        # Print the notification (doesn't block)
        print(f"[AgentDebug] {status['message']}", file=sys.stderr)


def assert_export_allowed():
    """Raise LicenseError if user tries to export without a license (F)."""
    if is_licensed():
        return
    raise LicenseError(
        f"🔒 Export and advanced features require an AgentDebug license.\n"
        f"Purchase at {PURCHASE_URL} for {LICENSE_PRICE} (one-time, forever).\n"
        f"Basic tracing continues to work — upgrade to unlock exports, HTML reports, "
        f"and the Team Dashboard."
    )


# ── Watermark (E) ──────────────────────────────────────────────────

def get_watermark_html() -> str:
    """Return an HTML watermark snippet for the dashboard (E).
    
    If licensed, returns empty string (no watermark).
    If trial, returns a subtle overlay.
    """
    if is_licensed():
        return ""
    
    remaining = check_trial().get("remaining", 0)
    if remaining > 0:
        return (
            f'<div style="position:fixed;bottom:8px;right:12px;z-index:9999;'
            f'font-size:11px;color:rgba(99,102,241,0.35);'
            f'font-family:monospace;letter-spacing:1px;user-select:none;'
            f'pointer-events:none;">'
            f'AgentDebug Trial · {remaining}/{TRIAL_LIMIT} uses left · '
            f'<a href="{PURCHASE_URL}" style="color:rgba(99,102,241,0.5);">Buy ${LICENSE_PRICE}</a>'
            f'</div>'
        )
    return ""


# ── CLI helpers ────────────────────────────────────────────────────

def format_trial_status() -> str:
    """Return a human-readable trial/license status string."""
    if is_licensed():
        return "✓ Licensed — all features unlocked"
    status = check_trial()
    remaining = status["remaining"]
    if remaining <= 0:
        return f"✗ Trial expired. Purchase at {PURCHASE_URL}"
    return f"📊 Trial: {remaining}/{TRIAL_LIMIT} uses remaining"


def reset_trial():
    """Reset trial counter (for testing)."""
    if _COUNTER_FILE.exists():
        _COUNTER_FILE.unlink()
    # Also remove license
    deactivate_license()
