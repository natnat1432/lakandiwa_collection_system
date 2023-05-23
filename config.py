from flask import Flask
from flask_sqlalchemy import SQLAlchemy



#app config
app  = Flask(__name__)
app.secret_key = "Lakandiwa2023"    
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///lakandiwa_collection.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#db config
db = SQLAlchemy(app)
