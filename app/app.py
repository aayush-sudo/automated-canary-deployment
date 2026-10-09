import os

from flask import Flask, jsonify

app = Flask(__name__)

APP_VERSION = os.getenv("APP_VERSION", "v1")


@app.route("/", methods=["GET"])
def home():
    if APP_VERSION == "v2":
        message = "Welcome to Canary Demo v2 - Improved Experience!"
    else:
        message = "Welcome to Canary Demo v1!"

    return jsonify({
        "application": "canary-demo",
        "version": APP_VERSION,
        "message": message
    }), 200


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "application": "canary-demo",
        "version": APP_VERSION
    }), 200


@app.route("/version", methods=["GET"])
def version():
    return jsonify({
        "application": "canary-demo",
        "version": APP_VERSION
    }), 200


if __name__ == "__main__":
    port = int(os.getenv("PORT","5001"))
    app.run(host="0.0.0.0", port=port)
