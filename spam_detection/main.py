import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# --- The code to load & train the model when the module is initialised ---

df = pd.read_csv("spam_detection/spam_list.csv")
df['label'] = df['label'].map({'ham': 0, 'spam': 1})

vectoriser = TfidfVectorizer(stop_words='english')
X = vectoriser.fit_transform(df['text'])

model = LogisticRegression()
model.fit(X, df['label'])


# --- The callable function ---

def get_spam_probability(message: str) -> float: # This is the callable function, for the spam detection check
    msg_tf = vectoriser.transform([message])
    return model.predict_proba(msg_tf)[0][1]