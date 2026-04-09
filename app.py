from flask import Flask, jsonify, send_from_directory

app = Flask(__name__)


@app.get("/")
def home():
    return send_from_directory(".", "index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})
