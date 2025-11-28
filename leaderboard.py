import json
import os

LEADERBOARD_FILE = os.path.join(os.path.dirname(__file__), "leaderboard.json")

# in-memory leaderboard: dict of difficulty -> list of {name, score}
leaderboard = {}

def _sanitize(data):
    # ensure difficulty keys exist and entries are well-formed
    # Support both survival and collector modes
    difficulties = ["Easy", "Normal", "Hard", "Easy-Collector", "Normal-Collector", "Hard-Collector"]
    for d in difficulties:
        if d not in data or not isinstance(data[d], list):
            data[d] = []
        cleaned = []
        for e in data[d][:10]:
            if isinstance(e, dict) and 'name' in e and 'score' in e:
                cleaned.append({'name': str(e['name'])[:32], 'score': int(e['score'])})
        cleaned.sort(key=lambda x: x['score'], reverse=True)
        data[d] = cleaned[:10]
    return data


def load_leaderboard():
    global leaderboard
    try:
        if os.path.exists(LEADERBOARD_FILE):
            with open(LEADERBOARD_FILE, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
                leaderboard = _sanitize(data)
                return
    except Exception:
        pass
    leaderboard = { 'Easy': [], 'Normal': [], 'Hard': [], 
                   'Easy-Collector': [], 'Normal-Collector': [], 'Hard-Collector': [] }


def save_leaderboard():
    try:
        with open(LEADERBOARD_FILE, 'w', encoding='utf-8') as fh:
            json.dump(leaderboard, fh, indent=2, ensure_ascii=False)
    except Exception:
        pass


def qualifies_for_leaderboard(difficulty, sc):
    lst = leaderboard.get(difficulty, [])
    if len(lst) < 10:
        return True
    return sc > (lst[-1]['score'] if lst else -1)


def add_score_to_leaderboard(difficulty, name, sc):
    lst = leaderboard.setdefault(difficulty, [])
    lst.append({'name': str(name)[:32], 'score': int(sc)})
    lst.sort(key=lambda x: x['score'], reverse=True)
    leaderboard[difficulty] = lst[:10]
    save_leaderboard()


def get_leaderboard(difficulty):
    return leaderboard.get(difficulty, [])

# auto-load on import
load_leaderboard()
