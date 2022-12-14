"""Logged-in page routes."""
from flask import Blueprint, render_template, redirect, url_for, session, flash, jsonify, request
from flask_login import login_required, logout_user, current_user
from datetime import datetime


from .forms import FeedbackForm, SearchForm
from .models import Feedback, Log, Food, Prod, log_food, db


# Blueprint Configuration
home_bp = Blueprint(
    'home_bp', __name__,
    template_folder='templates',
    static_folder='static'
)


@home_bp.route('/', methods=['GET', 'POST'])
def home():
    """
    User feedback.

    GET requests serve home page.
    POST requests validate form & receive feedback.
    """

    form = FeedbackForm()
    if form.validate_on_submit():
        feedback = Feedback(
            fullname=form.fullname.data,
            email=form.email.data,
            phone=form.phone.data,
            body=form.body.data
        )
        db.session.add(feedback)
        db.session.commit()
        flash("შეტყობინება მიღებულია!")
        return redirect(url_for("home_bp.home", form=form))
    
    return render_template(
        'home.html',
        form=form,
        title="Home page.",
        template="home-page",
        body="Home page."
    )   


@home_bp.route('/calculator', methods=['GET', 'POST'])
def calculator():
    """
    Calculator page.

    GET requests serve calculator page.
    POST requests receive user calories goal. (# Not implamented yet)
    """

    return render_template(
        'calculator.html',
        title="Calculator page.",
        template="calculator-page",
        body="Calculator page."
    )    


@home_bp.route('/calendar', methods=['GET'])
@login_required
def calendar():
    """
    Calendar page.

    GET requests serve calendar page.
    """

    user = current_user
    logs = Log.query.filter_by(usr=user).order_by(Log.date.desc()).all()

    log_dates = []

    for log in logs:
        cal = 0

        for prod in log.prods:
            cal += prod.cal

        log_dates.append({
            'log_date' : log,
            'cal' : cal
        })


    return render_template(
        'calendar.html',
        log_dates=log_dates,
        title="Calendar page.",
        template="calendar-page",
        body="Calendar page."
    )


@home_bp.route('/create_log', methods=['POST'])
@login_required
def create_log():
    """
    Create log.

    POST request add date to calendar page.
    """
    user = current_user
    date = request.form.get('date')

    if not date:
        flash('აირჩიეთ თარიღი', 'error')
        return redirect(url_for('home_bp.calendar'))

    log = Log(date=datetime.strptime(date, '%Y-%m-%d'), usr=user)

    db.session.add(log)
    db.session.commit()

    return redirect(url_for('home_bp.view', log_id=log.id))


@home_bp.route('/view/<int:log_id>', methods=['GET', 'POST'])
@login_required
def view(log_id):
    """
    Calendar view page.

    GET requests serve calendar view page.
    POST requests receive user calories input.
    """

    form = SearchForm()
    user = current_user
    log = Log.query.get_or_404(log_id)

    if user.id != log.user_id:
        return redirect(url_for('home_bp.calendar'))
    
    else:
        total = {
            'cal' : 0
        }

        for prod in log.prods:
            total['cal'] += prod.cal

        return render_template(
            'view.html',
            form=form,
            log=log,
            total=total,
            title="View page.",
            template="View-page",
            body="View page."
        )


@home_bp.route('/add_food_to_log/<int:log_id>', methods=['POST'])
@login_required
def add_food_to_log(log_id):

    log = Log.query.get_or_404(log_id)

    form = SearchForm()
    food_name = form.food.data
    food = Food.query.filter_by(name=food_name).first()

    gr = form.gr.data

    cal = gr * food.cal

    prod = Prod(name=food.name, cal=cal, gr=gr)
    db.session.add(prod)
    db.session.commit()

    add_food = log_food.insert().values(
        log_id=log.id,
        prod_id=prod.id
    )
    db.session.execute(add_food)
    db.session.commit()

    return redirect(url_for('home_bp.view', log_id=log_id))


@home_bp.route('/remove_food_from_log/<int:log_id>/<int:prod_id>')
@login_required
def remove_food_from_log(log_id, prod_id):

    log = Log.query.get(log_id)
    prod = Prod.query.get(prod_id)

    log.prods.remove(prod)
    db.session.commit()

    return redirect(url_for('home_bp.view', log_id=log_id))


@home_bp.route('/food', methods=['GET'])
@login_required
def fooddic():
    """
    For food search on view page.

    GET request search suggestions.
    """

    res = Food.query.all()
    list_food = [r.as_dict() for r in res]   
    
    return jsonify(list_food)


@home_bp.route('/logout')
@login_required
def logout():
    """User logout logic."""
    session.pop('user', None)
    logout_user()
    return redirect(url_for('auth_bp.login'))
