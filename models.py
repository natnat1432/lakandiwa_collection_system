from config import db



class User(db.Model):
    id = db.Column(db.String(8), primary_key = True)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    position = db.Column(db.String(255), nullable=False)


    def __init__(self,id,firstname,lastname,password, position):
        self.id = id
        self.firstname = firstname
        self.lastname = lastname
        self.password = password
        self.position = position


class Position(db.Model):
    position = db.Column(db.String(100), primary_key = True, unique=True)

    def __init__(self,position):
        self.position = position

        


