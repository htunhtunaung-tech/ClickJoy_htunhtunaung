# ==================== Data ====================
DATA_FILE = "data.csv"

ALL_DB_FIELDS = ["normal","flip","switch","pop","swap","cpm","stop",
                 "focus","chaos","memory","dopa","rcs"]

GAME_LIST = [
    ("normal", "Normal Click",   "⬡", "tap as fast as you can"),
    ("flip",   "Flip Coin",      "◆", "heads or tails?"),
    ("switch", "Switch",         "▣", "toggle the switch"),
    ("swap",   "Swap Click",     "◎", "chase the target"),
    ("cpm",    "Click per Time", "◷", "race the clock"),
    ("stop",   "Stopwatch",      "◉", "hit the exact time"),
    ("pop",    "Pop It",         "⬤", "pop every bubble fast!"),
    ("focus",  "Focus Burst",    "◈", "click only the right shape"),
    ("chaos",  "Chaos Control",  "⚡", "find the real button!"),
    ("memory", "Memory Flash",   "◫", "remember the pattern"),
    ("dopa",   "Dopamine Meter", "◑", "stay controlled, fill meter"),
    ("rcs",    "Color Shift",    "◐", "match the color — react fast"),
]

ICONS = {g[0]: g[2] for g in GAME_LIST}
NAMES = {g[0]: g[1] for g in GAME_LIST}
