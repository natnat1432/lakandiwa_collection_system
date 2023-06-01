from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify
from config import app
from config import db





@app.before_request
def create_tables():
    db.create_all()
    


@app.route('/')
def index():
    title = "Log in | Lakandiwa Collection System"
    message = request.args.get('message')

    if message != 'Invalid log in' and message is not None:
        return abort(404, "Page not found")
    return render_template("index.html", title=title, message=message)

@app.route('/login-validate', methods=['POST'])
def loginvalidate():
    userID = request.form['userID']
    password = request.form['password']

    if userID and password:
        if userID == '12345678' and password == 'lakandiwa@2023':
            print('log in')
    else:
        message="Invalid log in"
        return redirect(url_for('index', message=message))
    print(userID,password)


@app.route('/home')
def home():
    title = "Home | Lakandiwa Collection System"

    return render_template('home.html', title=title)

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')
  

