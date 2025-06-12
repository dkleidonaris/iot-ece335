import torch
import numpy as np
from torch import nn
from sklearn.preprocessing import StandardScaler
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 1. Ορισμός του μοντέλου (όπως πριν)
class IrrigationNet(nn.Module):
    def __init__(self, in_features):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(in_features, 32),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(16, 1)
        )

    def forward(self, x):
        return self.net(x)

# 2. Φόρτωση scaler parameters από JSON
with open(os.path.join(BASE_DIR, "scaler_params.json"), "r") as f:
    scaler_info = json.load(f)

training_means = np.array(scaler_info["mean"])
training_stds  = np.array(scaler_info["std"])

scaler = StandardScaler()
scaler.mean_ = training_means
scaler.scale_ = training_stds
scaler.var_ = training_stds ** 2
scaler.n_features_in_ = 4
# scaler.feature_names_in_ = np.array(['Temperature', 'Humidity', 'RainProbability', 'SunHours'])

# 3. Φόρτωση του μοντέλου
model = IrrigationNet(in_features=4)
weights_path = os.path.join(BASE_DIR, "best_model.pt")
state_dict = torch.load(weights_path, map_location=torch.device('cpu'), weights_only=True)
model.load_state_dict(state_dict)
model.eval()

# 4. Συνάρτηση πρόβλεψης
def predict(Temperature, Humidity, RainProbability, SunHours):
    input_data = np.array([[Temperature, Humidity, RainProbability, SunHours]], dtype=np.float32)
    input_scaled = scaler.transform(input_data)
    input_tensor = torch.from_numpy(input_scaled)
    
    with torch.no_grad():
        logits = model(input_tensor)
        probs = torch.sigmoid(logits)
        predicted = (probs > 0.5).float().item()
    
    return int(predicted), float(probs.item())

# 5. Παράδειγμα χρήσης
if __name__ == "__main__":
    pred, prob = predict(Temperature=23.1, Humidity=40.4, RainProbability=73.0, SunHours=8.9)
    print(f"Prediction: {'Water' if pred == 1 else 'Do not water'} (Confidence: {prob:.2f})")
