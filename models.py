from config import db
from datetime import datetime


class User(db.Model):
    id = db.Column(db.String(8), primary_key = True)
    firstname = db.Column(db.String(100), nullable=False)
    lastname = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    position = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(30), nullable=False)
    subsidy = db.relationship('Subsidy', backref='user', lazy=True)
    collection = db.relationship('Collection', backref='user', lazy=True)
    def __init__(self,id,firstname,lastname,password, position, status):
        self.id = id
        self.firstname = firstname
        self.lastname = lastname
        self.password = password
        self.position = position
        self.status = status

class Subsidy(db.Model):
    subsidy_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    member_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    clocked_start_date = db.Column(db.DateTime, nullable=True)
    end_date = db.Column(db.DateTime, nullable=False)
    clocked_end_date = db.Column(db.DateTime, nullable=True)
    subsidy_value = db.Column(db.Numeric(precision=10, scale=2), db.ForeignKey('subsidy_value.subsidy_value'), nullable=False)
    rendered_hours = db.Column(db.Time, nullable=True)
    #checked_by // EIC only
    def __init__(self, member_id, start_date, end_date):
        self.member_id = member_id
        self.start_date = start_date
        self.end_date = end_date
        subsidy_value = SubsidyValue.query.first()
        self.subsidy_value = subsidy_value.subsidy_value
        
class Collection(db.Model):
    acknowledgementID = db.Column(db.String(255), primary_key = True, unique = True)
    id_number = db.Column(db.String(8), nullable = False)
    student_firstname = db.Column(db.String(255), nullable = False)
    student_middlename = db.Column(db.String(255), nullable = True)
    student_lastname = db.Column(db.String(255), nullable = False)
    course = db.Column(db.String(55), nullable = False)
    year = db.Column(db.Integer, nullable = False)
    excempted_category = db.Column(db.String(55), nullable=True)
    member_id = db.Column(db.String(8), db.ForeignKey('user.id'), nullable=False)
    collection_value = db.Column(db.Numeric(precision=10, scale=2), db.ForeignKey('collection_value.collection_value'), nullable = False)
    voided = db.Column(db.String(12), nullable=False)
    #voided_at //datetime where book is voided
    created_at = db.Column(db.DateTime, nullable = False)

    def __init__(self, acknowledgementID, id_number, firstname, middlename, lastname, course, year, excempted_category, member_id):
        self.acknowledgementID = acknowledgementID
        self.id_number = id_number
        self.student_firstname = firstname
        self.student_middlename = middlename
        self.student_lastname = lastname
        self.course = course
        self.year = year
        self.excempted_category = excempted_category
        self.member_id = member_id
        collection_value = CollectionValue.query.first()
        self.collection_value = collection_value.collection_value
        self.voided = "no"
        self.created_at = datetime.now()

class SubsidyValue(db.Model):
    subsidy_value = db.Column(db.Numeric(precision=10, scale=2), nullable = False, unique = True, primary_key =True)
    subsidy = db.relationship('Subsidy', backref='SubsidyValue', lazy=True)
    def __init__(self, subsidy_value):
        self.subsidy_value = subsidy_value

class CollectionValue(db.Model):
    collection_value = db.Column(db.Numeric(precision=10, scale=2), nullable = False, unique = True, primary_key =True)
    collection = db.relationship('Collection', backref='CollectionValue', lazy=True)
    def __init__(self, collection_value):
        self.collection_value = collection_value


        


