"""Serves the dashboard, and rebuilds it with fresh OpenStreetMap drive times on request."""
import os

from flask import Flask, send_file

import model

app = Flask(__name__)
if not os.path.exists("index.html"):
    print("Building the model. This takes about 5 minutes the first time.")
    model.build()


@app.get("/")
def home():
    return send_file("index.html")


@app.post("/api/rebuild")
def rebuild():
    model.build()
    return {"done": True}


if __name__ == "__main__":
    app.run()
