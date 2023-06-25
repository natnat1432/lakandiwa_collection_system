from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify
from config import app
from config import db
from models import User,Subsidy,Collection,CollectionValue,SubsidyValue


from datetime import datetime, date, timedelta
from sqlalchemy import and_ ,func, extract

import environment

from util import getQuotes, formatTime, is_table_empty,DecimalEncoder

import json



def setSettings():
    if is_table_empty(SubsidyValue):
            subsidy_value = SubsidyValue(100.00)
            db.session.add(subsidy_value)
            db.session.commit()

    if is_table_empty(CollectionValue):
            collection_value = CollectionValue(100.00)
            db.session.add(collection_value)
            db.session.commit()

@app.template_filter('format_datetime')
def format_datetime(dt):
    return dt.strftime('%m-%d-%Y %I:%M %p')

@app.template_filter('date')
def date(dt):
    return dt.strftime('%m-%d-%Y')

@app.before_request
def create_tables():
    db.create_all()
    setSettings()

    
    


@app.route('/')
def index():
    if "position" in session:
        if session["position"] == "Admin":
            return redirect(url_for('users', message = "Welcome back"))
        else:
            return redirect(url_for('home', message = "Welcome back"))
        
    title = "Log in | Lakandiwa Collection System"
    message = request.args.get('message')
    messages = ["Invalid log in", "Logout successfully", "Login first"]
    if message is not None and message not in messages:
        return abort(404, "Page not found")
    return render_template("index.html", title=title, message=message)

@app.route('/login-validate', methods=['POST'])
def loginvalidate():
    userID = request.form['userID']
    password = request.form['password']

    if userID and password:
        check_user = User.query.filter_by(id=userID, password = password, status="active").first()
        if check_user:
            session['position'] = check_user.position
            session['user_firstname'] = check_user.firstname
            session['user_lastname'] = check_user.lastname
            session['user_id'] = check_user.id
            session['authenticated'] = True
            return redirect(url_for('home', message="Login successful"))
        else:
            if userID == '12345678' and password == 'lakandiwa@2023':
                session['position'] = "Admin"
                session['user_firstname'] = "Lakandiwa"
                session['user_lastname'] = "2023"
                session['user_id'] = 12345678
                session['authenticated'] = True
                return redirect(url_for('users', message="Login successful"))
            else:
                message="Invalid log in"
                return redirect(url_for('index', message=message))
                
            
    else:
        message="Invalid log in"
        return redirect(url_for('index', message=message))
    

def default_encoder(obj):
    return str(obj)


@app.route('/home')
def home():
    if "position" not in session:
        return redirect(url_for('index', message = "Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))
    
    title = "Home"
    quote = getQuotes()
    
    exist_subsidy = Subsidy.query.filter(
    and_(
        Subsidy.start_date <= datetime.now(),
        Subsidy.end_date >= datetime.now().date(),
        Subsidy.member_id == session['user_id']
        )
    ).first()

    collections = db.session.query(
    Collection.acknowledgementID,
    Collection.id_number,
    Collection.student_firstname,
    Collection.student_middlename,
    Collection.student_lastname,
    Collection.course,
    Collection.year,
    Collection.excempted_category,
    User.id,
    User.firstname,
    User.lastname,
    User.position,
    Collection.collection_value,
    Collection.voided,
    Collection.created_at
    ).join(User, User.id == Collection.member_id).order_by(Collection.created_at.desc()).filter(
        and_(
            func.date(Collection.created_at) == datetime.now().date(),
            Collection.member_id == session['user_id']
        )
    ).all()
    collections_dict = [collection._asdict() for collection in collections]


    print(json.dumps(collections_dict, indent=4, default=default_encoder)    )
    current_datetime = datetime.now()
    return render_template('home.html', title=title, course = environment.course, collections = collections,
                            exempted = environment.exempted, quote=quote, exist_subsidy = exist_subsidy, current_datetime = current_datetime)

@app.route('/clock_in')
def clock_in():
    if session['user_id'] is None:
        return redirect(url_for('index',message='Error clocking in. Logging in'))
    exist_subsidy = Subsidy.query.filter(
    and_(
        Subsidy.start_date <= datetime.now(),
        Subsidy.end_date >= datetime.now().date(),
        Subsidy.member_id == session['user_id']
        )
    ).first()

    exist_subsidy.clocked_start_date = datetime.now()
    db.session.commit()
    return redirect(url_for('home',message='Clocked in successfully'))
@app.route('/clock_out')
def clock_out():
    if session['user_id'] is None:
        return redirect(url_for('index',message='Error clocking in. Logging in'))
    exist_subsidy = Subsidy.query.filter(
        and_(
        Subsidy.start_date <= datetime.now(),
        Subsidy.end_date >= datetime.now().date(),
        Subsidy.member_id == session['user_id']
        )
    ).first()
    
    rendered_hours = datetime.now() - exist_subsidy.clocked_start_date
    total_hours = formatTime(rendered_hours)
    exist_subsidy.clocked_end_date = datetime.now()
    exist_subsidy.rendered_hours = total_hours
    db.session.commit()
    return redirect(url_for('home', message = 'Clocked out successfully'))
@app.route('/addcollection', methods=['POST'])
def addcollection():
    if "position" not in session:   
        return redirect(url_for('index', message = "Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))
    
    acknowledgementID   = request.form['acknowledgementID']
    id_number = request.form['id_number']
    firstname = request.form['firstname']
    middlename = request.form['middlename']
    lastname = request.form['lastname']
    course = request.form['course']
    year = request.form['year']

    exempted_checkbox = None
    exempted_category = None
    if 'exempted_checkbox' in request.form:
        exempted_checkbox = request.form['exempted_checkbox']
        exempted_category = request.form['exempted_category']

    if acknowledgementID and id_number and firstname and lastname and course and year:
        if exempted_checkbox == 'yes':
            exempted_category = request.form['exempted_category']
        
    else:
        return abort(404, "Page not found")

    add_collection = Collection(acknowledgementID, id_number, firstname, middlename,lastname,course,year,exempted_category,session['user_id'])
    db.session.add(add_collection)
    db.session.commit()

    return redirect(url_for('home', message='Student collection successfully added'))

@app.route('/subsidy')
def subsidy():
    if "position" not in session:
        return redirect(url_for('index', message = "Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))
    
    title = "Subsidy"
    message = request.args.get('message')
    members = User.query.filter_by(status="active").all()
    current_datetime = datetime.now().date()
    subsidy_amount = SubsidyValue.query.first()
    subsidies = db.session.query(Subsidy.subsidy_id,User.id,User.firstname,User.lastname, User.position, Subsidy.start_date, Subsidy.end_date, Subsidy.subsidy_value).join(Subsidy, User.id == Subsidy.member_id).order_by(Subsidy.subsidy_id.desc()).all()
    return render_template('subsidy.html', title=title, members=members, message = message, subsidies = subsidies, current_datetime = current_datetime, subsidy_amount = subsidy_amount.subsidy_value)
@app.route('/addsubsidy', methods=['POST'])
def addsubsidy():
    if "position" not in session:
        return redirect(url_for('index', message = "Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))
    
    member_id = request.form['member_id']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    message = None
    if member_id and start_date and end_date:

        if end_date < start_date:
            return redirect(url_for('subsidy', message = 'End date must not be earlier than startdate'))
        #Converting datetime-local format to MYSQL datetime format
        start_date = datetime.strptime(start_date,'%Y-%m-%dT%H:%M')

        end_date = datetime.strptime(end_date,'%Y-%m-%dT%H:%M')
        
        member = User.query.filter_by(id=member_id).first()

        if member:
            exist_subsidy = Subsidy.query.filter( (Subsidy.start_date <= start_date) & (Subsidy.end_date >= start_date), Subsidy.member_id == member_id).first()

            if exist_subsidy:
                message = "This member has a subsidy set within these schedule set"
            else:
                add_subsidy = Subsidy(member_id, start_date,end_date)
                db.session.add(add_subsidy)
                db.session.commit() 

                #add message successful adding subsidy
                message = "Subsidy added successfully"
        else:
            #add message to memeber error
            message = "Cannot add subsidy because member does not exist"
    else:
        #add message to incomplete fields
        message = "Cannot add subsidy if fields are empty"

    return redirect(url_for('subsidy', message=message))

@app.route('/editsubsidy', methods=['POST'])
def editsubsidy():
    if "position" not in session:
        return redirect(url_for('index', message = "Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))
    
    subsidy_id = request.form['edit_subsidy_id']
    member_id = request.form['edit_member_id']
    start_date = request.form['edit_start_date']
    end_date = request.form['edit_end_date']
    subsidy_value = request.form['edit_subsidy_value']
    start_date = datetime.strptime(start_date,'%Y-%m-%dT%H:%M')

    end_date = datetime.strptime(end_date,'%Y-%m-%dT%H:%M')
    message = None

    if subsidy_id and member_id and start_date and end_date and subsidy_value:
        subsidy = Subsidy.query.get(subsidy_id)
        subsidy.member_id = member_id
    
        subsidy.start_date = start_date
        subsidy.end_date = end_date
        subsidy.subsidy_value = subsidy_value
        db.session.commit()
        message = "Subsidy updated successfully"
        return redirect(url_for('subsidy', message=message))
    else:
        message = "Incomplete fields"
        return redirect(url_for('subsidy', message=message))

@app.route('/deletesubsidy/<subsidy_id>')
def deletesubsidy(subsidy_id:int):
    if "position" not in session:
        return redirect(url_for('index', message = "Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))
    
    subsidy = Subsidy.query.get(subsidy_id)
    message = "Error deleting subsidy"
    if subsidy:
        db.session.delete(subsidy)
        db.session.commit()
        message = "Subsidy deleted successfully"
    return redirect(url_for('subsidy', message = message))



@app.route('/users')
def users():
    if "position" not in session:
        return redirect(url_for('index', message = "Login first"))
    allowed = ['Editor in Chief', 'Managing Director', 'Admin']
    if session["position"] not in allowed:
        return redirect(url_for('users', message="Invalid page"))
    
    title = "Users"
    message = request.args.get('message')
    members = User.query.filter_by(status="active").all()
    return render_template('users.html', title=title, members=members, positions = environment.positions, message=message)

@app.route('/addmember', methods=['POST'])
def addmember():
    if "position" not in session:
        return redirect(url_for('index', message = "Login first"))
    allowed = ['Editor in Chief', 'Managing Director', 'Admin']
    if session["position"] not in allowed:
        return redirect(url_for('users', message="Invalid page"))
    id_number = request.form['id_number']
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    position = request.form['position']

    if id_number and firstname and lastname and position:
        if len(id_number) == 8 and position in environment.positions:
            existing_member = User.query.get(id_number)
            message = ""
            if existing_member:
                
                if existing_member.status == "deleted":
                    existing_member.status = "active"
                    db.session.commit()
                    message = "Member reactivated successfully"

                else:
                    message = "Member already exist"
                    
            else:
                new_member = User(id_number,firstname,lastname,environment.default_password, position, 'active')

                db.session.add(new_member)
                db.session.commit()
                message = "Member added successfully"

            return redirect(url_for("users", message=message))
        else:
            return abort(404,"Page not found")
    else:
        return abort(404,"Page not found")

@app.route('/editmember', methods=['POST'])
def editmember():
    if "position" not in session:
        return redirect(url_for('index', message = "Login first"))
    allowed = ['Editor in Chief', 'Managing Director', 'Admin']
    if session["position"] not in allowed:
        return redirect(url_for('users', message="Invalid page"))
    edit_id_number = request.form['edit_id_number']
    edit_firstname = request.form['edit_firstname']
    edit_lastname = request.form['edit_lastname']
    edit_position = request.form['edit_position'] 
    message = ""
    if edit_id_number and edit_firstname and edit_lastname and edit_position in environment.positions:
        edit_member = User.query.filter_by(id=edit_id_number).first()

        if edit_member: 
            edit_member.firstname = edit_firstname
            edit_member.lastname = edit_lastname
            edit_member.position = edit_position

            db.session.commit()
            message = "Member updated successfully"

        return redirect(url_for('users', message=message))
        
    else:
        return abort(404, "Page not found")
    
@app.route('/deletemember/<id_number>')
def deletemember(id_number:str):
    if "position" not in session:
        return redirect(url_for('index', message = "Login first"))
    allowed = ['Editor in Chief', 'Managing Director', 'Admin']
    if session["position"] not in allowed:
        return redirect(url_for('users', message="Invalid page"))
    user = User.query.filter_by(id=id_number, status="active").first()
    member = ""
    if user:
        user.status = "deleted"

        db.session.commit()
        message = "Member deleted successfully"
    else:
        member = "Error deleting member"
    
    return redirect(url_for('users', message=message))


@app.route('/reports')
def reports():
    if "position" not in session:
        return redirect(url_for('index', message = "Login first"))
    allowed_reports = ['Editor in Chief', 'Managing Director', 'Finance Manager']
    if session["position"] not in allowed_reports:
        if session["position"] == "Admin":
            return redirect(url_for('users', message="Invalid page"))
        else:
            return redirect(url_for('home', message="Invalid page"))
    
    title = "Reports"
    return render_template("reports.html", title=title)

@app.route('/settings')
def settings():
    if "position" not in session:
        return redirect(url_for('index', message = "Login first"))
    allowed_settings = ['Editor in Chief', 'Managing Director', 'Finance Manager']
    if session["position"] not in allowed_settings:
        if session["position"] == "Admin":
            return redirect(url_for('users', message="Invalid page"))
        else:
            return redirect(url_for('home', message="Invalid page"))
    collection_amount = CollectionValue.query.first()
    subsidy_amount = SubsidyValue.query.first()
    title = "Settings"
    return render_template("settings.html", title=title, collection_amount = collection_amount.collection_value, subsidy_amount = subsidy_amount.subsidy_value)
@app.route('/updatecollectionamount', methods=['POST'])
def updatecollectionamount():
    collection_value = request.form['collection_value']

    collection = CollectionValue.query.first()

    collection.collection_value = collection_value
    db.session.commit()
    return redirect(url_for('settings'))
@app.route('/updatesubsidyamount', methods=['POST'])
def updatesubsidyamount():
    subsidy_value = request.form['subsidy_value']

    subsidy = SubsidyValue.query.first()

    subsidy.subsidy_value = subsidy_value
    db.session.commit()
    return redirect(url_for('settings'))
@app.route('/logout')
def logout():
    session.clear()
    message = "Logout successfully"
    return redirect(url_for('index', message=message))


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers.add('Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0')   
    return response


if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0')
  

