from feature_extractor import extract_features
from flask import Flask,render_template,redirect,request,session
import pandas as pd
import joblib
import numpy as np
import os
import pickle

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
model = joblib.load(os.path.join(BASE_DIR, "models", "model1.pkl"))
feature_list = joblib.load(os.path.join(BASE_DIR, "models", "features.pkl"))

app = Flask(__name__)
app.secret_key = os.environ["SECRET_KEY"]

@app.route("/")
def Home():
    if "login" not in session:
        return redirect("/login")
    data = {"features": list(feature_list)}
    if "output" in session:
        data["output"] = session["output"]
        session.pop("output")
    return render_template("home.html", data=data)



@app.route("/login", methods=["GET", "POST"])
def Login():

    if request.method == "GET":
        return render_template("login.html")

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    # Demo credentials
    if username == "admin" and password == "password":
        session["login"] = True
        return redirect("/")

    # Invalid login
    return render_template(
        "login.html",
        Flag=True,
        Navigate=False,
        mymessage="❌ Invalid username or password. Please use the demo credentials provided."
    )


@app.route("/logout")
def logout():
    session.pop("login", None)
    return redirect("/login")


# Set your upload folder
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

from werkzeug.utils import secure_filename

@app.route("/predict", methods=["POST"])
def Predict():
    if 'file' not in request.files:
        return "No file part", 400

    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400

    filename = secure_filename(file.filename)
    filepath = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    # Remove existing file safely
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        return f"Failed to delete existing file: {e}", 500

    # Save uploaded file
    try:
        file.save(filepath)
    except Exception as e:
        return f"Failed to save file: {e}", 500

    # Extract features and predict
    extracted_features = extract_features(filepath)
    input_df = pd.DataFrame([extracted_features], columns=feature_list)

    pred = int(model.predict(input_df)[0])
    message = ("⚠️ Ransomware attack detected! Disconnect the device and start incident response."
               if pred == 0 else
               "✅ No ransomware detected. Keep your system up-to-date and monitor it regularly.")

    session["output"] = {"value": pred, "message": message}
    return redirect("/")



@app.route("/api/predict", methods=["POST"])
def PredictApi():
    if 'file' not in request.files:
        return {"error": "No file provided"}, 400

    file = request.files['file']
    if file.filename == '':
        return {"error": "No selected file"}, 400

    filename = secure_filename(file.filename)
    filepath = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], filename))

    try:
        if os.path.exists(filepath):
            os.remove(filepath)
        file.save(filepath)
    except Exception as e:
        return {"error": f"File error: {e}"}, 500

    extracted_features = extract_features(filepath)
    input_df = pd.DataFrame([extracted_features], columns=feature_list)

    pred = int(model.predict(input_df)[0])
    message = ("⚠️ Ransomware detected! Immediate action required."
               if pred == 0 else
               "✅ File is safe. No ransomware detected.")
    
    return {
        "value": pred,
        "output": "Attack Detected" if pred == 0 else "Not Detected",
        "message": message
    }



@app.route("/dashboard")
def Dashboard():
    if "login" not in session:
        return redirect("/login")
    return render_template("dashboard.html")

if __name__ == "__main__":
    app.run(debug=False)
