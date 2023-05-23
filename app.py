from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify
from config import app
from config import db





@app.before_request
def create_tables():
    db.create_all()
    


@app.route('/')
def index():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')
  

