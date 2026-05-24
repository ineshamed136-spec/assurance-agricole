import joblib
model = joblib.load("model.pkl")
print(model.feature_names_in_)
