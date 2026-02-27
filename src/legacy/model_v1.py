import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error
from sklearn.metrics import r2_score

df = pd.read_csv("combined_with_percentiles.csv")

percentile_cols =  [col for col in df.columns if "percentile" in col]

target = "goals_per_90_percentile"

# Split by league
train_df = df[df["league"] == "Bundesliga"]
test_df = df[df["league"] == "Premier League"]

X_train = train_df[percentile_cols].drop(columns=[target])
Y_train = train_df[target]

X_test = test_df[percentile_cols].drop(columns=[target])
y_test = test_df[target]

model = RandomForestRegressor(n_estimators=100,random_state=42)
model.fit(X_train,Y_train)

y_pred = model.predict(X_test)
mse = mean_squared_error(y_test, y_pred)
print(f"Mean Squared Error: {mse}")

r2 = r2_score(y_test, y_pred)
print("R2:", r2)

importances = model.feature_importances_
feature_importance_df = pd.DataFrame({
    "Feature": X_train.columns,
    "Importance": importances
}).sort_values(by="Importance", ascending=False)

print(feature_importance_df)
