import os
from game_data import DATA_FILE, ALL_DB_FIELDS

CSV_FIELDS = ["user","password","uid","total","normal","flip","switch","pop",
              "swap","cpm","stop","focus","chaos","memory","dopa","rcs","reward","bio","avatar"]
INT_FIELDS = {"total","normal","flip","switch","pop","swap","cpm","stop",
              "focus","chaos","memory","dopa","rcs"}

class DataManager:
    def __init__(self):
        import csv as _csv
        if not os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w", newline="", encoding="utf-8") as fh:
                _csv.DictWriter(fh, fieldnames=CSV_FIELDS).writeheader()

    def _read_all(self):
        import csv as _csv
        rows = []
        try:
            with open(DATA_FILE, "r", newline="", encoding="utf-8") as fh:
                reader = _csv.DictReader(fh)
                for row in reader:
                    r = dict(row)
                    for k in INT_FIELDS:
                        try: r[k] = int(r.get(k) or 0)
                        except ValueError: r[k] = 0
                    rw = r.get("reward", "")
                    r["reward"] = [x for x in rw.split("|") if x] if rw else []
                    r.setdefault("bio", ""); r.setdefault("avatar", "")
                    rows.append(r)
        except Exception:
            pass
        return rows

    def _write_all(self, rows):
        import csv as _csv
        with open(DATA_FILE, "w", newline="", encoding="utf-8") as fh:
            writer = _csv.DictWriter(fh, fieldnames=CSV_FIELDS, extrasaction="ignore")
            writer.writeheader()
            for r in rows:
                out = dict(r); out["reward"] = "|".join(r.get("reward", []))
                writer.writerow(out)

    def _next_uid(self, rows):
        if not rows: return "00000001"
        return str(max(int(r["uid"]) for r in rows) + 1).zfill(8)

    def register(self, username, password):
        rows = self._read_all()
        if any(r["user"] == username for r in rows): return False
        rows.append({"user": username, "password": password, "uid": self._next_uid(rows),
            "total": 0, "normal": 0, "flip": 0, "switch": 0, "pop": 0, "swap": 0,
            "cpm": 0, "stop": 0, "focus": 0, "chaos": 0, "memory": 0,
            "dopa": 0, "rcs": 0, "reward": [], "bio": "", "avatar": ""})
        self._write_all(rows); return True

    def login(self, username, password):
        for r in self._read_all():
            if r["user"] == username and r["password"] == password: return r
        return None

    def get_user(self, username):
        for r in self._read_all():
            if r["user"] == username: return r
        return None

    def update_score(self, username, field, value):
        rows = self._read_all()
        for r in rows:
            if r["user"] == username:
                r[field] = value
                r["total"] = sum(r.get(f, 0) for f in ALL_DB_FIELDS)
                break
        self._write_all(rows)

    def update_bio(self, username, bio):
        rows = self._read_all()
        for r in rows:
            if r["user"] == username: r["bio"] = bio; break
        self._write_all(rows)

    def update_avatar(self, username, avatar_path):
        rows = self._read_all()
        for r in rows:
            if r["user"] == username: r["avatar"] = avatar_path; break
        self._write_all(rows)

    def add_reward(self, username, reward_id):
        rows = self._read_all()
        for r in rows:
            if r["user"] == username:
                if reward_id not in r["reward"]: r["reward"].append(reward_id)
                break
        self._write_all(rows)

    def has_reward(self, username, reward_id):
        u = self.get_user(username)
        return bool(u) and reward_id in u["reward"]

    def get_all_scores(self, field):
        rows = self._read_all()
        result = [(r["user"], r.get(field, 0)) for r in rows]
        result.sort(key=lambda x: x[1], reverse=True)
        return result

    def get_reward_percent(self, reward_id):
        rows = self._read_all()
        if not rows: return 0.0
        return sum(1 for r in rows if reward_id in r["reward"]) / len(rows) * 100.0
