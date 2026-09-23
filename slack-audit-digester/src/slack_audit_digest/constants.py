"""Lookback thresholds and product constants. Tune here, document in README."""

from __future__ import annotations

DEFAULT_LOOKBACK_DAYS = 45
MAX_LOOKBACK_DAYS = 90
THIN_HUMAN_MESSAGES = 40
THIN_ACTIVE_DAYS = 10
MAX_OPPORTUNITIES = 5
MIN_CLUSTER_MESSAGES = 3
MIN_CLUSTER_DAYS = 2
SKU_DEFAULT = "slack-opportunity-audit"

# Product prices from the locked one-pager. Do not invent new SKUs.
AUDIT_PRICE = "$299"
FORWARD_WATCH_PRICE = "$99"
FORWARD_WATCH_DURATION = "2-week"
SETUP_PRICE = "$799"
SETUP_CREDIT = "$150"
SETUP_CREDIT_CODE = "AUDIT150"
SETUP_CREDIT_WINDOW = "30 days"

FORWARD_WATCH_URL = "https://buy.stripe.com/cNibJ1f2VeUW4VD7TPdAk0g"
LANDING_URL = "https://tindogdigital.tech/slack-audit/"

SYSTEM_SUBTYPES = frozenset(
    {
        "bot_message",
        "channel_join",
        "channel_leave",
        "channel_topic",
        "channel_purpose",
        "channel_name",
        "channel_archive",
        "channel_unarchive",
        "pinned_item",
        "unpinned_item",
        "reminder_add",
        "bot_add",
        "bot_remove",
        "ekm_access_denied",
        "channel_posting_permissions",
        "group_join",
        "group_leave",
        "message_deleted",
        "tombstone",
        "channel_canvas_updated",
        "joiner_notification",
        "sh_room_created",
        "huddle_thread",
        "channel_convert_to_private",
        "channel_convert_to_public",
    }
)

BOT_USER_IDS = frozenset({"USLACKBOT"})
