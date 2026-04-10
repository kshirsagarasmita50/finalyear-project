import pandas as pd
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# ---------------- DATASET ----------------
data = [
    ("Scientists discover a new planet that supports life in our solar system","REAL"),
    ("Breaking: Celebrity caught in scandal involving aliens from Mars","FAKE"),
    ("Government announces new policy to support small businesses","REAL"),
    ("Doctors warn that drinking cold water causes cancer","FAKE"),
    ("Researchers find ancient city under the Sahara Desert","REAL"),
    ("Facebook shutting down permanently next week, company confirms","FAKE"),
    ("New technology reduces electricity usage by 40% in homes","REAL"),
    ("Python snake found driving a car in Mumbai, shocking locals","FAKE"),
    ("University develops vaccine that shows 95% success rate","REAL"),
    ("Whales found flying in the sky above Japan after earthquake","FAKE"),
    ("National Holiday On Tuesday","FAKE"),
    ("Today Is Monday","REAL")
]

df = pd.DataFrame(data, columns=["text", "label"])

# ---------------- TRAIN MODEL ----------------
X = df["text"]
y = df["label"].map({"FAKE":0, "REAL":1})

vectorizer = TfidfVectorizer(stop_words="english")
X_vec = vectorizer.fit_transform(X)

model = LogisticRegression()
model.fit(X_vec, y)

# ---------------- SAVE FILES ----------------
joblib.dump(model, "model.pkl")
joblib.dump(vectorizer, "vectorizer.pkl")

print("Model & Vectorizer saved successfully!")