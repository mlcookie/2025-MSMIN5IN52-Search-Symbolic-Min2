import requests
from collections import defaultdict, Counter

###########################################################
# 1) WORDLE-KAPPA API (only using POST /{guess})
###########################################################

API_GUESS = "https://wordle-api-kappa.vercel.app/"

def get_feedback_from_api(guess):
    """Call Wordle API to get feedback for the guess."""
    r = requests.post(API_GUESS + guess).json()

    if not r.get("is_word_in_list", True):
        return None

    if r.get("is_correct", False):
        return "GGGGG"

    fb = []
    for info in r["character_info"]:
        if info["scoring"]["correct_idx"]:
            fb.append("G")
        elif info["scoring"]["in_word"]:
            fb.append("Y")
        else:
            fb.append("B")

    return "".join(fb)

###########################################################
# 2) LOAD OFFICIAL WORDLIST
###########################################################

WORDLIST_URL = "https://raw.githubusercontent.com/Kinkelin/WordleCompetition/main/data/official/combined_wordlist.txt"

def load_wordlist():
    words = requests.get(WORDLIST_URL).text.splitlines()
    words = [w.strip().lower() for w in words if len(w) == 5]
    print(f"Loaded {len(words)} words from official list.")
    return words

###########################################################
# 3) CSP SOLVER
###########################################################

class WordleSolver:
    def __init__(self, wordlist):
        self.candidates = list(wordlist)
        self.fixed = {}
        self.forbidden_pos = defaultdict(set)
        self.min_count = defaultdict(int)
        self.max_count = {}

    def apply_feedback(self, guess, fb):
        seen = defaultdict(int)
        for ch, f in zip(guess, fb):
            if f in "GY":
                seen[ch] += 1
        for ch, n in seen.items():
            self.min_count[ch] = max(self.min_count[ch], n)

        for i, (g, f) in enumerate(zip(guess, fb)):
            if f == 'G':
                self.fixed[i] = g
            elif f == 'Y':
                self.forbidden_pos[i].add(g)
            elif f == 'B':
                if self.min_count[g] == 0:
                    self.max_count[g] = 0
                else:
                    self.max_count[g] = self.min_count[g]
                self.forbidden_pos[i].add(g)

        self.filter()

    def matches(self, word):
        for i, l in self.fixed.items():
            if word[i] != l:
                return False
        for i, forb in self.forbidden_pos.items():
            if word[i] in forb:
                return False

        wc = Counter(word)
        for ch, c in self.min_count.items():
            if wc[ch] < c:
                return False
        for ch, c in self.max_count.items():
            if wc[ch] > c:
                return False

        return True

    def filter(self):
        self.candidates = [w for w in self.candidates if self.matches(w)]

    def suggest(self):
        freq = Counter()
        for w in self.candidates:
            for ch in set(w):
                freq[ch] += 1

        scored = []
        for w in self.candidates:
            score = sum(freq[ch] for ch in set(w))
            scored.append((score, w))

        scored.sort(reverse=True)
        return [w for _, w in scored[:5]]

###########################################################
# 4) MAIN LOOP (does NOT know the answer)
###########################################################

def main():
    print("=== WORDLE SOLVER — no cheating ===\n")

    wordlist = load_wordlist()
    solver = WordleSolver(wordlist)

    guess = "crane"  # very strong opener
    step = 1

    while True:
        print(f"\nGuess #{step}: {guess.upper()}")
        fb = get_feedback_from_api(guess)
        print("Feedback:", fb)

        if fb == "GGGGG":
            print("\n🎉 Solved! Word =", guess.upper())
            break

        solver.apply_feedback(guess, fb)
        print(f"Remaining candidates: {len(solver.candidates)}")

        suggestions = solver.suggest()
        print("Suggestions:", suggestions)

        guess = suggestions[0]
        step += 1

if __name__ == "__main__":
    main()
