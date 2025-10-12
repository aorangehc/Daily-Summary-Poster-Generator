from typing import Dict

DEFAULT_THEME_ID = "black_gold"

THEMES: Dict[str, dict] = {
    "black_gold": {
        "palette": {
            "background": "#0F0F0F",
            "primary": "#D4AF37",
            "text": "#EDEDED",
            "muted": "#858585",
            "accent": "#6C5CE7",
            "card": "#1a1a1a",
            "card_border": "#2a2a2a",
        },
        "tokens": {
            "radius": 20,
            "gap": 24,
            "column_gap": 40,
            "card_padding": 24,
        },
    },
    "morandi_cream": {
        "palette": {
            "background": "#F3F1ED",
            "primary": "#BEB4A7",
            "text": "#2B2B2B",
            "accent": "#D4A5A5",
            "muted": "#6B7F94",
            "card": "#FFFFFF",
            "card_border": "#E4E1DC",
        },
        "tokens": {"radius": 20, "gap": 24, "column_gap": 40, "card_padding": 24},
    },
    "mist_blueviolet": {
        "palette": {
            "background": "#101522",
            "primary": "#7A88FF",
            "text": "#ECEFF4",
            "accent": "#D0A2F7",
            "muted": "#7C8190",
            "card": "#151a2b",
            "card_border": "#22273a",
        },
        "tokens": {"radius": 20, "gap": 24, "column_gap": 40, "card_padding": 24},
    },
    "fresh_summer": {
        "palette": {
            "background": "#F2FBF7",
            "primary": "#2BB673",
            "text": "#22303C",
            "accent": "#00B8D9",
            "muted": "#6B7F94",
            "card": "#FFFFFF",
            "card_border": "#DAE6E0",
        },
        "tokens": {"radius": 20, "gap": 24, "column_gap": 40, "card_padding": 24},
    },
}

