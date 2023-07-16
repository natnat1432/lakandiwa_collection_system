from flask import Flask, render_template, request, redirect, url_for, session, abort, jsonify
from config import app
from config import db
from models import User, Subsidy, Collection, CollectionValue, SubsidyValue


from datetime import datetime, date, timedelta
from sqlalchemy import and_, func, extract, or_

import environment

from util import getQuotes, formatTime, is_table_empty, DecimalEncoder, toDateTime, getnametodict

import json

import calendar
import pandas as pd


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


@app.template_filter('month_word')
def month_word(dt):
    return calendar.month_name[int(dt)]


@app.template_filter('format_currency')
def format_currency(value):
    return '{:,.2f}'.format(value)


@app.before_request
def create_tables():
    db.create_all()
    setSettings()


@app.route('/')
def index():
    if "position" in session:
        if session["position"] == "Admin":
            return redirect(url_for('users', message="Welcome back"))
        else:
            return redirect(url_for('home', message="Welcome back"))

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
        check_user = User.query.filter_by(
            id=userID, password=password, status="active").first()
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
                message = "Invalid log in"
                return redirect(url_for('index', message=message))

    else:
        message = "Invalid log in"
        return redirect(url_for('index', message=message))


def default_encoder(obj):
    return str(obj)


@app.route('/home')
def home():
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))

    title = "Home"
    quote = getQuotes()
    message = request.args.get('message')

    date_variable = datetime.datetime.now().date()

    # filter variables
    search_query = None
    sort_filter = None
    student_filter = None
    excempted_filter = None
    course_filter = None
    year_filter = None
    void_filter = None

    search_query = request.args.get('search_query')
    sort_filter = request.args.get('sort_filter')
    student_filter = request.args.get('student_filter')
    excempted_filter = request.args.get('excempted_filter')
    course_filter = request.args.get('course_filter')
    year_filter = request.args.get('year_filter')
    void_filter = request.args.get('void_filter')

    if not sort_filter:
        sort_filter = 'desc'
    if not student_filter:
        student_filter = 'all'
    if not excempted_filter:
        excempted_filter = None

    if not course_filter:
        course_filter = 'all'
    if not year_filter:
        year_filter = 'all'
    if not void_filter:
        void_filter = 'all'

    if not search_query:
        search_query = ''

    current_datetime = datetime.datetime.now()

    exist_subsidy = Subsidy.query.filter(
        and_(
            Subsidy.start_date <= datetime.datetime.now(),
            Subsidy.end_date >= datetime.datetime.now().date(),
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
    ).join(User, User.id == Collection.member_id).filter(
        and_(
            func.date(Collection.created_at) == current_datetime.date(),
            Collection.member_id == session['user_id'],
            or_(
                Collection.acknowledgementID.ilike(f"%{search_query}%"),
                Collection.id_number.ilike(f"%{search_query}%"),
                Collection.student_firstname.ilike(f"%{search_query}%"),
                Collection.student_middlename.ilike(f"%{search_query}%"),
                Collection.student_lastname.ilike(f"%{search_query}%")
            )
        ),
        or_(
            Collection.excempted_category.isnot(
                None) if student_filter == 'excempted' and excempted_filter == 'all' else None,
            Collection.excempted_category.is_(
                excempted_filter) if student_filter == 'excempted' and excempted_filter != 'all' else None,
            Collection.excempted_category.is_(
                None) if student_filter == 'not_excempted' else None,
            Collection.excempted_category.is_(
                None) if student_filter == 'all' else None,
            Collection.excempted_category.isnot(
                None) if student_filter == 'all' else None,
        ),
        or_(
            Collection.course.is_(
                course_filter) if course_filter != 'all' else None,
            Collection.course.isnot(None) if course_filter == 'all' else None,
        ),
        or_(
            Collection.year.is_(year_filter) if year_filter != 'all' else None,
            Collection.year.isnot(None) if year_filter == 'all' else None,
        ),
        or_(
            Collection.voided.is_(
                void_filter) if void_filter != 'all' else None,
            Collection.voided.isnot(None) if void_filter == 'all' else None,
        )
    ).order_by(Collection.created_at.desc() if sort_filter == 'desc' else Collection.created_at).all()

    total_receipts = db.session.query(func.count()).select_from(Collection).filter(func.date(Collection.created_at) == date_variable).scalar()
    total_exempted = db.session.query(func.count()).select_from(Collection).filter(and_(func.date(Collection.created_at) == date_variable, Collection.excempted_category.isnot(None), Collection.voided.is_('no'))).scalar()
    total_voided = db.session.query(func.count()).select_from(Collection).filter(and_(func.date(Collection.created_at) == date_variable, Collection.voided.is_('yes'))).scalar()
    total_number_of_receipts = db.session.query(func.count()).select_from(Collection).filter(and_(func.date(Collection.created_at) == date_variable, Collection.excempted_category.is_(None), Collection.voided.is_('no'))).scalar()
    total_subsidy = 0
    total_amount_to_be_collected = db.session.query(func.coalesce(func.sum(Collection.collection_value),0)).filter(and_(func.date(Collection.created_at) == date_variable, Collection.excempted_category.is_(None), Collection.voided.is_('no'))).scalar()
    total_cash_on_hand = total_amount_to_be_collected
    authorized_member = db.session.query(
        Subsidy.subsidy_id,
        User.id,
        User.firstname,
        User.lastname,
        User.position,
        Subsidy.start_date,
        Subsidy.clocked_start_date,
        Subsidy.clocked_end_date,
        Subsidy.rendered_hours,
        Subsidy.end_date,
        Subsidy.subsidy_value,
        Subsidy.signed_by
    ).join(User, User.id == Subsidy.member_id).filter(func.date(Subsidy.start_date) == date_variable).all()
    for each in authorized_member:
        if each.signed_by is not None:
            if total_cash_on_hand is None:
                total_cash_on_hand = 0
            if total_cash_on_hand >= each.subsidy_value and total_cash_on_hand is not None and each.subsidy_value is not None:
                total_cash_on_hand = total_cash_on_hand - each.subsidy_value
            total_subsidy = total_subsidy + each.subsidy_value

    


    return render_template('home.html', title=title, course=environment.course, collections=collections, message=message,
                           total_receipts = total_receipts, total_excempted = total_exempted, total_voided=total_voided, total_number_of_receipts=total_number_of_receipts, total_subsidy=total_subsidy, total_amount_to_be_collected=total_amount_to_be_collected, total_cash_on_hand=total_cash_on_hand,
                           authorized_member=authorized_member,search_query=search_query, sort_filter=sort_filter, student_filter=student_filter, excempted_filter=excempted_filter, course_filter=course_filter, year_filter=year_filter, void_filter=void_filter,
                           exempted=environment.exempted, quote=quote, exist_subsidy=exist_subsidy, current_datetime=current_datetime)


@app.route('/clock_in')
def clock_in():
    if session['user_id'] is None:
        return redirect(url_for('index', message='Error clocking in. Logging in'))
    exist_subsidy = Subsidy.query.filter(
        and_(
            Subsidy.start_date <= datetime.datetime.now(),
            Subsidy.end_date >= datetime.datetime.now().date(),
            Subsidy.member_id == session['user_id']
        )
    ).first()

    exist_subsidy.clocked_start_date = datetime.datetime.now()
    db.session.commit()
    return redirect(url_for('home', message='Clocked in successfully'))


@app.route('/voidticket', methods=['POST'])
def voidticket():
    ackID = request.form['void_ticket_input']

    check_collection = Collection.query.filter_by(
        acknowledgementID=ackID).first()

    if check_collection:
        if check_collection.voided == 'yes':
            check_collection.voided = 'no'
        else:
            check_collection.voided = 'yes'
        db.session.commit()
        return redirect(url_for('home', message='Ticket void successfully updated'))
    else:
        return redirect(url_for('home', message='Ticket does not exist'))


@app.route('/voidticketdayreport', methods=['POST'])
def voidticketdayreport():
    ackID = request.form['void_ticket_input']
    date = request.form['distinct_date']
    day = request.form['distinct_day']
    check_collection = Collection.query.filter_by(
        acknowledgementID=ackID).first()

    if check_collection:
        if check_collection.voided == 'yes':
            check_collection.voided = 'no'
        else:
            check_collection.voided = 'yes'
        db.session.commit()
        return redirect(url_for('daymonthreport', distinct_date=date, distinct_day=day, message='Ticket void successfully updated'))
    else:
        return redirect(url_for('daymonthreport', distinct_date=date, distinct_day=day, message='Ticket does not exist'))


@app.route('/voidticketallreport', methods=['POST'])
def voidticketallreport():
    ackID = request.form['void_ticket_input']

    check_collection = Collection.query.filter_by(
        acknowledgementID=ackID).first()

    if check_collection:
        if check_collection.voided == 'yes':
            check_collection.voided = 'no'
        else:
            check_collection.voided = 'yes'
        db.session.commit()
        return redirect(url_for('allreports', message='Ticket void successfully updated'))
    else:
        return redirect(url_for('allreports', message='Ticket does not exist'))


@app.route('/clock_out')
def clock_out():
    if session['user_id'] is None:
        return redirect(url_for('index', message='Error clocking in. Logging in'))
    exist_subsidy = Subsidy.query.filter(
        and_(
            Subsidy.start_date <= datetime.datetime.now(),
            Subsidy.end_date >= datetime.datetime.now().date(),
            Subsidy.member_id == session['user_id']
        )
    ).first()

    rendered_hours = datetime.datetime.now() - exist_subsidy.clocked_start_date
    total_hours = formatTime(rendered_hours)
    exist_subsidy.clocked_end_date = datetime.datetime.now()
    exist_subsidy.rendered_hours = total_hours
    db.session.commit()
    return redirect(url_for('home', message='Clocked out successfully'))


@app.route('/addcollection', methods=['POST'])
def addcollection():
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))

    acknowledgementID = request.form['acknowledgementID']
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

    add_collection = Collection(acknowledgementID, id_number, firstname, middlename, lastname, course, year, exempted_category, session['user_id'])
    db.session.add(add_collection)
    db.session.commit()

    return redirect(url_for('home', message='Student collection successfully added'))


@app.route('/addcollectiondayreport', methods=['POST'])
def addcollectiondayreport():
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))

    acknowledgementID = request.form['acknowledgementID']
    id_number = request.form['id_number']
    firstname = request.form['firstname']
    middlename = request.form['middlename']
    lastname = request.form['lastname']
    course = request.form['course']
    year = request.form['year']

    date = request.form['distinct_date']
    day = request.form['distinct_day']

    date_variable = datetime.datetime.strptime(f'{date}-{day}', '%Y-%m-%d').date()

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

    addCol = Collection(acknowledgementID, id_number, firstname, middlename, lastname, course, year, exempted_category, session['user_id'])
    db.session.add(addCol)
    db.session.commit()

    exist_col = Collection.query.filter_by(acknowledgementID = acknowledgementID).first()
    if exist_col:
        exist_col.created_at = date_variable
        db.session.commit()


    return redirect(url_for('daymonthreport', distinct_day=day, distinct_date=date, message='Student collection successfully added'))


@app.route('/addcollectionallreport', methods=['POST'])
def addcollectionallreport():
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))

    acknowledgementID = request.form['acknowledgementID']
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

    add_collection = Collection(acknowledgementID, id_number, firstname,
                                middlename, lastname, course, year, exempted_category, session['user_id'])
    db.session.add(add_collection)
    db.session.commit()

    return redirect(url_for('allreports', message='Student collection successfully added'))


@app.route('/editcollection', methods=['POST'])
def editcollection():
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))

    acknowledgementID = request.form['acknowledgementID']
    id_number = request.form['id_number']
    firstname = request.form['firstname']
    middlename = request.form['middlename']
    lastname = request.form['lastname']
    course = request.form['course']
    year = request.form['year']
    exempted_checkbox = None
    exempted_category = None

    if acknowledgementID and id_number and firstname and lastname and course and year:
        if exempted_checkbox == 'yes':
            exempted_category = request.form['exempted_category']

    else:
        return abort(404, "Page not found")

    edit_collection = Collection.query.filter_by(
        acknowledgementID=acknowledgementID).first()
    if edit_collection:
        edit_collection.id_number = id_number
        edit_collection.student_firstname = firstname
        edit_collection.student_middlename = middlename
        edit_collection.student_lastname = lastname
        edit_collection.course = course
        edit_collection.year = year
        edit_collection.excempted_category = exempted_category
        db.session.commit()

        return redirect(url_for('home', message='Record updated successfully'))
    else:
        return redirect(url_for('home', message='Collection not found'))


@app.route('/editcollectiondayreport', methods=['POST'])
def editcollectiondayreport():
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))

    acknowledgementID = request.form['acknowledgementID']
    id_number = request.form['id_number']
    firstname = request.form['firstname']
    middlename = request.form['middlename']
    lastname = request.form['lastname']
    course = request.form['course']
    year = request.form['year']
    exempted_checkbox = None
    exempted_category = None
    date = request.form['distinct_date']
    day = request.form['distinct_day']

    if acknowledgementID and id_number and firstname and lastname and course and year:
        if exempted_checkbox == 'yes':
            exempted_category = request.form['exempted_category']

    else:
        return abort(404, "Page not found")

    edit_collection = Collection.query.filter_by(
        acknowledgementID=acknowledgementID).first()
    if edit_collection:
        edit_collection.id_number = id_number
        edit_collection.student_firstname = firstname
        edit_collection.student_middlename = middlename
        edit_collection.student_lastname = lastname
        edit_collection.course = course
        edit_collection.year = year
        edit_collection.excempted_category = exempted_category
        db.session.commit()

        return redirect(url_for('daymonthreport', distinct_date=date, distinct_day=day, message='Record updated successfully'))
    else:
        return redirect(url_for('daymonthreport', distinct_date=date, distinct_day=day, message='Collection not found'))


@app.route('/editcollectionallreport', methods=['POST'])
def editcollectionallreport():
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))

    acknowledgementID = request.form['acknowledgementID']
    id_number = request.form['id_number']
    firstname = request.form['firstname']
    middlename = request.form['middlename']
    lastname = request.form['lastname']
    course = request.form['course']
    year = request.form['year']
    exempted_checkbox = None
    exempted_category = None

    if acknowledgementID and id_number and firstname and lastname and course and year:
        if exempted_checkbox == 'yes':
            exempted_category = request.form['exempted_category']

    else:
        return abort(404, "Page not found")

    edit_collection = Collection.query.filter_by(
        acknowledgementID=acknowledgementID).first()
    if edit_collection:
        edit_collection.id_number = id_number
        edit_collection.student_firstname = firstname
        edit_collection.student_middlename = middlename
        edit_collection.student_lastname = lastname
        edit_collection.course = course
        edit_collection.year = year
        edit_collection.excempted_category = exempted_category
        db.session.commit()

        return redirect(url_for('allreports', message='Record updated successfully'))
    else:
        return redirect(url_for('allreports', message='Collection not found'))


@app.route('/subsidy')
def subsidy():
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))

    title = "Subsidy"
    message = request.args.get('message')
    members = User.query.filter_by(status="active").all()
    current_datetime = datetime.datetime.now().date()
    subsidy_amount = SubsidyValue.query.first()
    subsidies = db.session.query(Subsidy.subsidy_id, User.id, User.firstname, User.lastname, User.position, Subsidy.start_date,
                                 Subsidy.end_date, Subsidy.clocked_start_date, Subsidy.clocked_end_date, Subsidy.rendered_hours, Subsidy.subsidy_value, Subsidy.signed_by, Subsidy.role).join(Subsidy, User.id == Subsidy.member_id).order_by(Subsidy.subsidy_id.desc()).all()
    return render_template('subsidy.html', title=title, members=members, message=message, subsidies=subsidies, current_datetime=current_datetime, subsidy_amount=subsidy_amount.subsidy_value)


@app.route('/addsubsidy', methods=['POST'])
def addsubsidy():
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))

    member_id = request.form['member_id']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    role = request.form['role']
    message = None
    if member_id and start_date and end_date:

        if end_date < start_date:
            return redirect(url_for('subsidy', message='End date must not be earlier than startdate'))
        # Converting datetime-local format to MYSQL datetime format
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%dT%H:%M')

        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%dT%H:%M')

        member = User.query.filter_by(id=member_id).first()

        if member:
            exist_subsidy = Subsidy.query.filter((Subsidy.start_date <= start_date) & (
                Subsidy.end_date >= start_date), Subsidy.member_id == member_id).first()

            if exist_subsidy:
                message = "This member has a subsidy set within these schedule set"
            else:
                add_subsidy = Subsidy(member_id, role, start_date, end_date)
                db.session.add(add_subsidy)
                db.session.commit()

                # add message successful adding subsidy
                message = "Subsidy added successfully"
        else:
            # add message to memeber error
            message = "Cannot add subsidy because member does not exist"
    else:
        # add message to incomplete fields
        message = "Cannot add subsidy if fields are empty"

    return redirect(url_for('subsidy', message=message))


@app.route('/editsubsidy', methods=['POST'])
def editsubsidy():
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))

    subsidy_id = request.form['edit_subsidy_id']
    member_id = request.form['edit_member_id']
    start_date = request.form['edit_start_date']
    end_date = request.form['edit_end_date']
    subsidy_value = request.form['edit_subsidy_value']
    start_date = datetime.datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
    role = request.form['edit_role']
    end_date = datetime.datetime.strptime(end_date, '%Y-%m-%dT%H:%M')
    message = None

    if subsidy_id and member_id and start_date and end_date and subsidy_value:
        subsidy = Subsidy.query.get(subsidy_id)
        subsidy.member_id = member_id

        subsidy.start_date = start_date
        subsidy.end_date = end_date
        subsidy.subsidy_value = subsidy_value
        subsidy.role = role
        db.session.commit()
        message = "Subsidy updated successfully"
        return redirect(url_for('subsidy', message=message))
    else:
        message = "Incomplete fields"
        return redirect(url_for('subsidy', message=message))


@app.route('/deletesubsidy/<subsidy_id>')
def deletesubsidy(subsidy_id: int):
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))

    subsidy = Subsidy.query.get(subsidy_id)
    message = "Error deleting subsidy"
    if subsidy:
        db.session.delete(subsidy)
        db.session.commit()
        message = "Subsidy deleted successfully"
    return redirect(url_for('subsidy', message=message))


@app.route('/signsubsidy/<subsidy_id>')
def signsubsidy(subsidy_id: str):
    if not subsidy_id:
        return redirect(url_for('subsidy', message='Subsidy ID not found'))
    allowed = ['Editor in Chief', 'Managing Director']

    if session['position'] not in allowed:
        return redirect(url_for('subsidy', message='Not authorized to sign'))

    exist_subsidy = Subsidy.query.filter_by(subsidy_id=subsidy_id).first()

    if exist_subsidy:
        exist_subsidy.signed_by = session['user_id']
        db.session.commit()
        return redirect(url_for('subsidy', message='Subsidy signed successfully'))
    else:
        return redirect(url_for('subsidy', message='Subsidy not found'))


@app.route('/users')
def users():
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
    allowed = ['Editor in Chief', 'Managing Director', 'Admin']
    if session["position"] not in allowed:
        return redirect(url_for('users', message="Invalid page"))

    title = "Users"
    message = request.args.get('message')
    members = User.query.filter_by(status="active").all()
    return render_template('users.html', title=title, members=members, positions=environment.positions, message=message)


@app.route('/addmember', methods=['POST'])
def addmember():
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
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
                new_member = User(id_number, firstname, lastname,
                                  environment.default_password, position, 'active')

                db.session.add(new_member)
                db.session.commit()
                message = "Member added successfully"

            return redirect(url_for("users", message=message))
        else:
            return abort(404, "Page not found")
    else:
        return abort(404, "Page not found")


@app.route('/editmember', methods=['POST'])
def editmember():
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
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
def deletemember(id_number: str):
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
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
        return redirect(url_for('index', message="Login first"))
    allowed_reports = ['Editor in Chief',
                       'Managing Director', 'Finance Manager']
    if session["position"] not in allowed_reports:
        if session["position"] == "Admin":
            return redirect(url_for('users', message="Invalid page"))
        else:
            return redirect(url_for('home', message="Invalid page"))

    distinct_dates = Collection.query.with_entities(
        extract('month', Collection.created_at).label('month'),
        extract('year', Collection.created_at).label('year'),
    ).distinct().order_by('year', 'month').all()
    title = "Reports"
    members = db.session.query(User).all()
    message = request.args.get('message')
    return render_template("reports.html", title=title, distinct_dates=distinct_dates, members=members, message=message)


@app.route('/reports/<distinct_date>')
def monthreport(distinct_date: str):
    temp = distinct_date.split('-')
    distinct_days = Collection.query.filter(
        extract('month', Collection.created_at) == temp[1],
        extract('year', Collection.created_at) == temp[0]
    ).with_entities(
        extract('day', Collection.created_at).label('day')
    ).distinct().order_by('day').all()
    title = f'{month_word(int(temp[1]))} {temp[0]} Report'
    return render_template('monthreport.html', distinct_days=distinct_days, distinct_date=temp, title=title)


@app.route('/reports/<distinct_date>/<distinct_day>')
def daymonthreport(distinct_date: str, distinct_day: str):
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))

    temp = distinct_date.split('-')

    date_string = f'{distinct_date}-{distinct_day}'
    date_variable = datetime.datetime.strptime(date_string, '%Y-%m-%d').date()

    title = f"{month_word(int(temp[1]))} {distinct_day}, {temp[0]}"
    message = request.args.get('message')

    # filter variables
    search_query = None
    sort_filter = None
    student_filter = None
    excempted_filter = None
    course_filter = None
    year_filter = None
    void_filter = None

    search_query = request.args.get('search_query')
    sort_filter = request.args.get('sort_filter')
    student_filter = request.args.get('student_filter')
    excempted_filter = request.args.get('excempted_filter')
    course_filter = request.args.get('course_filter')
    year_filter = request.args.get('year_filter')
    void_filter = request.args.get('void_filter')

    if not sort_filter:
        sort_filter = 'desc'
    if not student_filter:
        student_filter = 'all'
    if not excempted_filter:
        excempted_filter = None

    if not course_filter:
        course_filter = 'all'
    if not year_filter:
        year_filter = 'all'
    if not void_filter:
        void_filter = 'all'

    if not search_query:
        search_query = ''

    current_datetime = datetime.datetime.now()

    exist_subsidy = Subsidy.query.filter(
        and_(
            Subsidy.start_date <= datetime.datetime.now(),
            Subsidy.end_date >= datetime.datetime.now().date(),
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
    ).join(User, User.id == Collection.member_id).filter(
        and_(
            func.date(Collection.created_at) == date_variable,
            or_(
                Collection.acknowledgementID.ilike(f"%{search_query}%"),
                Collection.id_number.ilike(f"%{search_query}%"),
                Collection.student_firstname.ilike(f"%{search_query}%"),
                Collection.student_middlename.ilike(f"%{search_query}%"),
                Collection.student_lastname.ilike(f"%{search_query}%")
            )
        ),
        or_(
            Collection.excempted_category.isnot(
                None) if student_filter == 'excempted' and excempted_filter == 'all' else None,
            Collection.excempted_category.is_(
                excempted_filter) if student_filter == 'excempted' and excempted_filter != 'all' else None,
            Collection.excempted_category.is_(
                None) if student_filter == 'not_excempted' else None,
            Collection.excempted_category.is_(
                None) if student_filter == 'all' else None,
            Collection.excempted_category.isnot(
                None) if student_filter == 'all' else None,
        ),
        or_(
            Collection.course.is_(
                course_filter) if course_filter != 'all' else None,
            Collection.course.isnot(None) if course_filter == 'all' else None,
        ),
        or_(
            Collection.year.is_(year_filter) if year_filter != 'all' else None,
            Collection.year.isnot(None) if year_filter == 'all' else None,
        ),
        or_(
            Collection.voided.is_(
                void_filter) if void_filter != 'all' else None,
            Collection.voided.isnot(None) if void_filter == 'all' else None,
        )
    ).order_by(Collection.created_at.desc() if sort_filter == 'desc' else Collection.created_at).all()

    total_receipts = db.session.query(func.count()).select_from(Collection).filter(
        func.date(Collection.created_at) == date_variable).scalar()
    total_exempted = db.session.query(func.count()).select_from(Collection).filter(and_(func.date(
        Collection.created_at) == date_variable, Collection.excempted_category.isnot(None), Collection.voided.is_('no'))).scalar()
    total_voided = db.session.query(func.count()).select_from(Collection).filter(and_(
        func.date(Collection.created_at) == date_variable, Collection.voided.is_('yes'))).scalar()
    total_number_of_receipts = db.session.query(func.count()).select_from(Collection).filter(and_(func.date(
        Collection.created_at) == date_variable, Collection.excempted_category.is_(None), Collection.voided.is_('no'))).scalar()
    total_subsidy = 0
    total_amount_to_be_collected = db.session.query(func.coalesce(func.sum(Collection.collection_value),0)).filter(and_(func.date(
        Collection.created_at) == date_variable, Collection.excempted_category.is_(None), Collection.voided.is_('no'))).scalar()
    total_cash_on_hand = total_amount_to_be_collected
    authorized_member = db.session.query(
        Subsidy.subsidy_id,
        User.id,
        User.firstname,
        User.lastname,
        User.position,
        Subsidy.start_date,
        Subsidy.clocked_start_date,
        Subsidy.clocked_end_date,
        Subsidy.rendered_hours,
        Subsidy.end_date,
        Subsidy.subsidy_value,
        Subsidy.signed_by
    ).join(User, User.id == Subsidy.member_id).filter(func.date(Subsidy.start_date) == date_variable).all()
    for each in authorized_member:
        if each.signed_by is not None:
            if total_cash_on_hand is None:
                total_cash_on_hand = 0
            if total_cash_on_hand >= each.subsidy_value and total_cash_on_hand is not None and each.subsidy_value is not None:
                total_cash_on_hand = total_cash_on_hand - each.subsidy_value
            total_subsidy = total_subsidy + each.subsidy_value

    members = User.query.all()

    return render_template('dayreport.html', title=title, course=environment.course,  collections=collections, message=message, total_receipts=total_receipts, total_excempted=total_exempted, total_number_of_receipts=total_number_of_receipts, total_amount_to_be_collected=total_amount_to_be_collected, total_cash_on_hand=total_cash_on_hand, authorized_member=authorized_member, total_subsidy=total_subsidy,
                           search_query=search_query, sort_filter=sort_filter, student_filter=student_filter, excempted_filter=excempted_filter, course_filter=course_filter, year_filter=year_filter, void_filter=void_filter, members=members, total_voided=total_voided,
                           exempted=environment.exempted, exist_subsidy=exist_subsidy, current_datetime=current_datetime, distinct_date=distinct_date, distinct_day=distinct_day)


@app.route('/allreports')
def allreports():
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
    if session["position"] == "Admin":
        return redirect(url_for('users', message="Invalid page"))

    title = "All Records"
    message = request.args.get('message')

    # filter variables
    search_query = None
    sort_filter = None
    student_filter = None
    excempted_filter = None
    course_filter = None
    year_filter = None
    void_filter = None

    search_query = request.args.get('search_query')
    sort_filter = request.args.get('sort_filter')
    student_filter = request.args.get('student_filter')
    excempted_filter = request.args.get('excempted_filter')
    course_filter = request.args.get('course_filter')
    year_filter = request.args.get('year_filter')
    void_filter = request.args.get('void_filter')

    if not sort_filter:
        sort_filter = 'desc'
    if not student_filter:
        student_filter = 'all'
    if not excempted_filter:
        excempted_filter = None

    if not course_filter:
        course_filter = 'all'
    if not year_filter:
        year_filter = 'all'
    if not void_filter:
        void_filter = 'all'

    if not search_query:
        search_query = ''

    current_datetime = datetime.datetime.now()

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
    ).join(User, User.id == Collection.member_id).filter(
        and_(
            # func.date(Collection.created_at) == date_variable,
            or_(
                Collection.acknowledgementID.ilike(f"%{search_query}%"),
                Collection.id_number.ilike(f"%{search_query}%"),
                Collection.student_firstname.ilike(f"%{search_query}%"),
                Collection.student_middlename.ilike(f"%{search_query}%"),
                Collection.student_lastname.ilike(f"%{search_query}%")
            )
        ),
        or_(
            Collection.excempted_category.isnot(
                None) if student_filter == 'excempted' and excempted_filter == 'all' else None,
            Collection.excempted_category.is_(
                excempted_filter) if student_filter == 'excempted' and excempted_filter != 'all' else None,
            Collection.excempted_category.is_(
                None) if student_filter == 'not_excempted' else None,
            Collection.excempted_category.is_(
                None) if student_filter == 'all' else None,
            Collection.excempted_category.isnot(
                None) if student_filter == 'all' else None,
        ),
        or_(
            Collection.course.is_(
                course_filter) if course_filter != 'all' else None,
            Collection.course.isnot(None) if course_filter == 'all' else None,
        ),
        or_(
            Collection.year.is_(year_filter) if year_filter != 'all' else None,
            Collection.year.isnot(None) if year_filter == 'all' else None,
        ),
        or_(
            Collection.voided.is_(
                void_filter) if void_filter != 'all' else None,
            Collection.voided.isnot(None) if void_filter == 'all' else None,
        )
    ).order_by(Collection.created_at.desc() if sort_filter == 'desc' else Collection.created_at).all()

    total_receipts = db.session.query(
        func.count()).select_from(Collection).scalar()
    total_exempted = db.session.query(func.count()).select_from(Collection).filter(
        and_(Collection.excempted_category.isnot(None), Collection.voided.is_('no'))).scalar()
    total_voided = db.session.query(func.count()).select_from(
        Collection).filter(and_(Collection.voided.is_('yes'))).scalar()
    total_number_of_receipts = db.session.query(func.count()).select_from(Collection).filter(
        and_(Collection.excempted_category.is_(None), Collection.voided.is_('no'))).scalar()
    total_subsidy = 0
    total_amount_to_be_collected = db.session.query(func.coalesce(func.sum(Collection.collection_value),0)).filter(
        and_(Collection.excempted_category.is_(None), Collection.voided.is_('no'))).scalar()
    total_cash_on_hand = total_amount_to_be_collected
    authorized_member = db.session.query(
        Subsidy.subsidy_id,
        User.id,
        User.firstname,
        User.lastname,
        User.position,
        Subsidy.start_date,
        Subsidy.clocked_start_date,
        Subsidy.clocked_end_date,
        Subsidy.rendered_hours,
        Subsidy.end_date,
        Subsidy.subsidy_value,
        Subsidy.signed_by
    ).join(User, User.id == Subsidy.member_id).all()
    for each in authorized_member:
        if each.signed_by is not None:
            if total_cash_on_hand is None:
                total_cash_on_hand = 0
            if total_cash_on_hand >= each.subsidy_value and total_cash_on_hand is not None and each.subsidy_value is not None:
                total_cash_on_hand = total_cash_on_hand - each.subsidy_value
            total_subsidy = total_subsidy + each.subsidy_value

    members = User.query.all()

    return render_template('allreports.html', title=title, course=environment.course,  collections=collections, message=message, total_receipts=total_receipts, total_excempted=total_exempted, total_number_of_receipts=total_number_of_receipts, total_amount_to_be_collected=total_amount_to_be_collected, total_cash_on_hand=total_cash_on_hand, authorized_member=authorized_member, total_subsidy=total_subsidy,
                           search_query=search_query, sort_filter=sort_filter, student_filter=student_filter, excempted_filter=excempted_filter, course_filter=course_filter, year_filter=year_filter, void_filter=void_filter, members=members, total_voided=total_voided,
                           exempted=environment.exempted, current_datetime=current_datetime)

import datetime

@app.route('/importdata', methods=['POST'])
def importdata():
    member_id = request.form.getlist('member_id[]')
    start_date = request.form.getlist('start_date[]')
    clocked_start_date = request.form.getlist('clocked_start_date[]')
    end_date = request.form.getlist('end_date[]')
    clocked_end_date = request.form.getlist('clocked_end_date[]')
    subsidy_value = request.form.getlist('subsidy_value[]')
    role = request.form.getlist('role[]')

    file = request.files['excelFile']

    if file:
        encoder_id = None
        import_date =  datetime.datetime.strptime(start_date[0], '%Y-%m-%dT%H:%M').date()
        for i in range(len(member_id)):

            # Convert string values to datetime objects
            start_datetime = datetime.datetime.strptime(start_date[i], '%Y-%m-%dT%H:%M')
            end_datetime = datetime.datetime.strptime(end_date[i], '%Y-%m-%dT%H:%M')

            # Create the Subsidy object with datetime values
            addsub = Subsidy(member_id[i], role[i], start_datetime, end_datetime)
            db.session.add(addsub)
            db.session.commit()

            existing_sub = Subsidy.query.filter_by(member_id=member_id[i], role=role[i], start_date=start_datetime, end_date=end_datetime).first()

            if existing_sub:
                rendered_hours = toDateTime(clocked_end_date[i]) - toDateTime(clocked_start_date[i])

                eic = User.query.filter_by(position='Editor in Chief').first()

                existing_sub.clocked_start_date = toDateTime(clocked_start_date[i])
                existing_sub.clocked_end_date = toDateTime(clocked_end_date[i])
                existing_sub.subsidy_value = subsidy_value[i]
                existing_sub.rendered_hours = formatTime(rendered_hours)
                existing_sub.signed_by = eic.id
                db.session.commit()

        for i in range(len(member_id)):
            if role[i] == 'encoder':
                encoder_id = member_id[i]
                break
        if encoder_id is None:
            encoder_id = member_id[0]

        df = pd.read_excel(file, sheet_name='Sheet1')
        for index, each in df.iterrows():
            for i in range(len(each)):
                if str(each[i]) == 'nan':
                    each[i] = None
            acknowledgementID = each[3].replace('No.', '').strip()

            name = getnametodict(str(each[0]))

            if name is not None:
                new_collection = Collection(acknowledgementID, each[1], name['firstname'], name['middlename'], name['lastname'], each[2].split('-')[0], each[2].split('-')[1], each[4], encoder_id)
                db.session.add(new_collection)
                db.session.commit()
            else:
                new_collection = Collection(acknowledgementID, each[1], each[0].split(',')[1], '', each[0].split(',')[0], each[2].split('-')[0], each[2].split('-')[1], each[4], encoder_id)
                db.session.add(new_collection)
                db.session.commit()
            existing_collection = Collection.query.filter_by(acknowledgementID=acknowledgementID).first()
            existing_collection.created_at = import_date
            existing_collection.voided = each[5]
            db.session.commit()

    return redirect(url_for('reports', message='Excel imported successfully'))



@app.route('/settings')
def settings():
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
    allowed_settings = ['Editor in Chief',
                        'Managing Director', 'Finance Manager']
    if session["position"] not in allowed_settings:
        if session["position"] == "Admin":
            return redirect(url_for('users', message="Invalid page"))
        else:
            return redirect(url_for('home', message="Invalid page"))
    collection_amount = CollectionValue.query.first()
    subsidy_amount = SubsidyValue.query.first()
    title = "Settings"
    message = request.args.get('message')
    return render_template("settings.html", title=title, collection_amount=collection_amount.collection_value, subsidy_amount=subsidy_amount.subsidy_value, message=message)


@app.route('/usersettings')
def usersettings():
    if "position" not in session:
        return redirect(url_for('index', message="Login first"))
    if session['position'] == 'Admin':
        return redirect(url_for('users', message="Invalid page"))

    title = "User Settings"
    message = request.args.get('message')
    return render_template('usersettings.html', title=title, message=message)


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


@app.route('/changepassword', methods=['POST'])
def changepassword():
    if 'position' in session and session['position'] == 'Admin':
        return abort(404, "Admin cannot change password")

    if 'user_id' in session and session['position'] != 'Admin':
        user_id = session['user_id']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        check_user = User.query.filter_by(id=user_id).first()

        if check_user:
            if (new_password == confirm_password):
                check_user.password = new_password
                db.session.commit()
                return redirect(url_for('usersettings', message='Password changed successfully'))
            else:
                return redirect(url_for('usersettings', message='Passwords are not equal'))
        else:
            return abort(404, "User not found")


@app.route('/deletecollection', methods=['POST'])
def deletecollection():
    collection_id = request.form['delete_collection_id']

    check_collection = Collection.query.filter_by(
        acknowledgementID=collection_id).first()
    if check_collection:
        db.session.delete(check_collection)
        db.session.commit()

        return redirect(url_for('home', message='Collection record deleted successfully'))
    else:
        return redirect(url_for('home', message='Collection record does not exist'))


@app.route('/deletecollectiondayreport', methods=['POST'])
def deletecollectiondayreport():
    collection_id = request.form['delete_collection_id']
    date = request.form['distinct_date']
    day = request.form['distinct_day']
    check_collection = Collection.query.filter_by(
        acknowledgementID=collection_id).first()
    if check_collection:
        db.session.delete(check_collection)
        db.session.commit()

        return redirect(url_for('daymonthreport', distinct_day=day, distinct_date=date, message='Collection record deleted successfully'))
    else:
        return redirect(url_for('daymonthreport', distinct_day=day, distinct_date=date, message='Collection record does not exist'))


@app.route('/deletecollectionallreport', methods=['POST'])
def deletecollectionallreport():
    collection_id = request.form['delete_collection_id']

    check_collection = Collection.query.filter_by(
        acknowledgementID=collection_id).first()
    if check_collection:
        db.session.delete(check_collection)
        db.session.commit()

        return redirect(url_for('allreports', message='Collection record deleted successfully'))
    else:
        return redirect(url_for('allreports', message='Collection record does not exist'))


@app.route('/logout')
def logout():
    session.clear()
    message = "Logout successfully"
    return redirect(url_for('index', message=message))


@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers.add(
        'Cache-Control', 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0')
    return response


if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0')
