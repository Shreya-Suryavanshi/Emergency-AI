from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import pickle
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent

texts = []
labels = []

def add(category: str, examples: list[str]):
    for t in examples:
        texts.append(t)
        labels.append(category)

# 🔥 Fire Emergency
add("fire", [
    "house fire", "there is a house fire", "my house is on fire", "kitchen fire",
    "gas explosion", "cylinder blast", "gas exploded", "gas leak caught fire",
    "forest fire", "wildfire nearby", "trees are burning",
    "electrical fire", "short circuit fire", "wiring is burning", "electric panel fire",
    "smoke in building", "fire in apartment", "flames visible"
])

# 🚑 Medical Emergency
add("medical", [
    "heart attack", "chest pain and breathlessness", "possible heart attack",
    "road accident injury", "accident happened someone injured", "bike crash injuries", "car accident injured",
    "unconscious person", "not responding", "fainted and unconscious",
    "severe bleeding", "heavy bleeding", "blood loss", "cut wound bleeding",
    "broken bone", "fracture", "burn injury", "poisoning"
])

# 🚓 Police / Crime Emergency
add("police", [
    "theft / robbery", "robbery happening", "someone stole my phone", "burglary",
    "physical assault", "someone is attacking", "fight and assault",
    "domestic violence", "abuse at home", "husband beating wife",
    "kidnapping", "child kidnapped", "person abducted",
    "stalking", "threatening call", "intruder in house"
])

# 🌊 Natural Disaster Emergency
add("natural_disaster", [
    "flood", "flood water entering house", "area is flooded", "flash flood",
    "earthquake", "earthquake shaking", "building shaking earthquake",
    "cyclone / storm", "severe storm", "cyclone warning", "strong winds and storm",
    "landslide", "landslide blocked road", "rocks falling landslide",
    "tsunami warning", "dam overflow", "heavy rain disaster"
])

# ⚡ Utility / Infrastructure Emergency
add("utility", [
    "electric shock", "someone got electric shock", "electrocuted",
    "gas leakage", "smell of gas leak", "gas leak in kitchen", "gas pipe leaking",
    "power failure", "no electricity", "blackout in area", "transformer blast",
    "water pipeline burst", "water pipe burst", "major water leakage",
    "building collapse", "bridge collapse", "road blocked due to damage"
])

vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(texts)

model = MultinomialNB()
model.fit(X, labels)

with (BACKEND_DIR / "model.pkl").open("wb") as f:
    pickle.dump((model, vectorizer), f)