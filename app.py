# -*- coding: utf-8 -*-
"""app.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1CSKMeXdYwXMD1PCdShE7JJ7fKUxrxtgj
"""

from flask import Flask, request, jsonify
import torch
from torch import nn
import numpy as np
import joblib  # If scaler is saved using joblib
from sklearn.preprocessing import MinMaxScaler

# Initialize Flask app
app = Flask(__name__)

# Load the saved LSTM model
class LSTMModel(nn.Module):
    def __init__(self, input_size=1, hidden_size=50, num_layers=2, output_size=1):
        super(LSTMModel, self).__init__()
        self.lstm = nn.LSTM(input_size, hidden_size, num_layers, batch_first=True)
        self.fc = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        out, _ = self.lstm(x)
        out = self.fc(out[:, -1, :])  # Take the last output
        return out

model = LSTMModel()
model.load_state_dict(torch.load("model.pth"))
model.eval()

# Load the scaler
scaler = joblib.load("scaler.pkl")  # Ensure scaler.pkl exists

@app.route('/predict', methods=['POST'])
def predict():
    # Parse input JSON
    input_data = request.json.get("temperature_sequence", [])
    if not input_data or len(input_data) != 24:
        return jsonify({"error": "Invalid input. Expecting 24 temperature values."}), 400

    # Preprocess input
    input_data = np.array(input_data).reshape(1, -1, 1)  # Reshape for LSTM
    input_data_scaled = scaler.transform(input_data.reshape(-1, 1)).reshape(1, -1, 1)
    input_tensor = torch.Tensor(input_data_scaled)

    # Make prediction
    with torch.no_grad():
        prediction = model(input_tensor).item()

    # Rescale prediction
    prediction_rescaled = scaler.inverse_transform([[prediction]])[0][0]

    return jsonify({"predicted_temperature": round(prediction_rescaled, 2)})

if __name__ == '__main__':
    app.run(debug=True)