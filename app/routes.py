# routes.py
# from datetime import date, datetime
import datetime
from dateutil.relativedelta import relativedelta
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from sqlalchemy import asc, desc, extract, func, literal, and_, or_
from werkzeug.urls import url_parse

from app import app, db
from app.forms import EditProfileForm, LoginForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from app.email import send_password_reset_email
from app.models import Fitness, Fitstory, Typefit, User, user_fit


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.datetime.utcnow()
        db.session.commit()


@app.route('/cloneitem/<int:id>', methods=["POST", "GET"])
def cloneitem(id):
    today = datetime.date.today()
    if request.method == "POST":
        thisdate = request.form["itemdate"]
        thistype = request.form["stype"]
        thistype_id = Typefit.query.with_entities(Typefit.id).filter(Typefit.typedet == thistype).first()[0]
        thissummary = request.form["summary"]
        thisstory = request.form["storydet"]
        thismiles = request.form["miles"]
        thisstats = request.form["stats"]
        thisminutes = request.form["minutes"]
        newfit = Fitness(date=thisdate, summary=thissummary, type_id=thistype_id, miles=thismiles, stats=thisstats,
                         minutes=thisminutes)
        newfit.users.clear()
        users_set = request.form.getlist("username")
        for user in users_set:
            user = User.query.filter_by(username=user).first()
            newfit.users.append(user)
        if thisstory and thisstory != "None":
            newstory = Fitstory(storydet=thisstory)
            newfit.story_fit.append(newstory)
        db.session.add(newfit)
        db.session.commit()
        return redirect('/index')
    else:
        stypes = [value for (value,) in Typefit.query.with_entities(Typefit.typedet).all()]
        thisitem = Fitness.query.get(id)
        users_set = [value for (value,) in User.query.join(user_fit).join(Fitness).with_entities(User.username).filter(
            Fitness.id == id).all()]
        users_all = [value for (value,) in User.query.with_entities(User.username).order_by(User.username).all()]
        item = Fitness.query.join(Typefit).outerjoin(Fitstory).with_entities(
            Fitness.id, Fitness.date,
            Typefit.typedet, Fitness.summary,
            Fitness.miles, Fitness.stats,
            Fitness.minutes, Fitstory.storydet).filter(Fitness.id == ('{}'.format(id))).first()
        typename = item.typedet
        if item is None:
            flash('N')
            return redirect(url_for('index'))
    return render_template('cloneitem.html', title='clone', stypes=stypes, users_set=users_set, today=today,
                           users_all=users_all, typename=typename, item=item)


@app.route('/deleteitem/<int:id>')
def deleteitem(id):
    delete_item = Fitness.query.get(id)
    delete_story = Fitstory.query.filter(Fitstory.fit_id == ('{}'.format(id))).first()
    if delete_story is not None:
        db.session.delete(delete_story)
    db.session.delete(delete_item)
    db.session.commit()
    return redirect(url_for('index'))


@app.route('/edititem/<int:id>', methods=["POST", "GET"])
def edititem(id):
    today = datetime.date.today()
    if request.method == "POST":
        update_item = Fitness.query.get(id)
        update_item.date = request.form["itemdate"]
        thistype = request.form["stype"]
        thistype_id = Typefit.query.with_entities(Typefit.id).filter(Typefit.typedet == thistype).first()[0]
        update_item.type_id = thistype_id
        update_item.summary = request.form["summary"]
        update_item.miles = request.form["miles"]
        update_item.stats = request.form["stats"]
        update_item.minutes = request.form["minutes"]
        thisstory = request.form["storydet"]
        update_item.users.clear()
        users_set = request.form.getlist("username")
        for user in users_set:
            user = User.query.filter_by(username=user).first()
            update_item.users.append(user)
        if thisstory and thisstory != "None":
            update_story = Fitstory.query.filter(Fitstory.fit_id == ('{}'.format(id))).first()
            update_story.storydet = thisstory
        db.session.commit()
        return redirect('/index')
    else:
        stypes = [value for (value,) in Typefit.query.with_entities(Typefit.typedet).all()]
        users_set = [value for (value,) in User.query.join(user_fit).join(Fitness).with_entities(User.username).filter(
            Fitness.id == id).all()]
        users_all = [value for (value,) in User.query.with_entities(User.username).order_by(User.username).all()]
        item = Fitness.query.join(Typefit).outerjoin(Fitstory).with_entities(
            Fitness.id, Fitness.date,
            Typefit.typedet, Fitness.summary,
            Fitness.miles, Fitness.stats,
            Fitness.minutes, Fitstory.storydet).filter(
            Fitness.id == ('{}'.format(id))).first()
        typename = item.typedet
        if item is None:
            flash('N')
            return redirect(url_for('index'))
    return render_template('edititem.html', title='edit', stypes=stypes, users_set=users_set, today=today,
                           users_all=users_all, typename=typename, item=item)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
    return render_template('signin/edit_profile.html', title='Edit Profile', form=form)


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@login_required
def index():
    if request.method == "POST":
        seltype = request.form["filter"]
        items = Fitness.query.join(Typefit).outerjoin(Fitstory).with_entities(
            Fitness.id,
            Fitness.date,
            Typefit.typedet,
            Fitness.summary,
            Fitness.miles,
            Fitness.stats,
            Fitness.minutes,
            Fitstory.storydet).filter(
            Typefit.typedet.ilike('%{}%'.format(seltype))).order_by(desc(Fitness.date)).limit(50).all()
        title = seltype
    else:
        items = Fitness.query.join(Typefit).outerjoin(Fitstory).with_entities(
            Fitness.id,
            Fitness.date,
            Typefit.typedet,
            Fitness.summary,
            Fitness.miles,
            Fitness.stats,
            Fitness.minutes,
            Fitstory.storydet).order_by(
            desc(Fitness.date)).limit(50).all()
        title = 'All items'

    # to get the list of usernames for each item:
    # 1. get a list of all the `Fitness.id`s returned by the query
    fitness_ids = [item[0] for item in items]
    # 2. get a list of `User.username`s by joining via `user_fit` onto `User`s
    list_usernames = Fitness.query.join(user_fit).join(User).with_entities(
        Fitness.id,
        User.username).filter(Fitness.id.in_(fitness_ids)).order_by(
        desc(Fitness.id), asc(User.username)).all()
    # 3. create a dict indexed by `Fitness.id` for quick look-up
    dict_usernames = dict()
    for id in fitness_ids:
        dict_usernames[id] = []
    for row in list_usernames:
        dict_usernames[row[0]].append(row)

    return render_template('index.html', title=title, items=items, dict_usernames=dict_usernames)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(next_page)
    return render_template('signin/login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/newitem', methods=['GET', 'POST'])
def newitem():
    today = datetime.date.today()
    if request.method == "POST":
        thisdate = request.form["itemdate"]
        thistype = request.form["stype"]
        thistype_id = Typefit.query.with_entities(Typefit.id).filter(Typefit.typedet == thistype).first()[0]
        thissummary = request.form["summary"]
        thisstory = request.form["storydet"]
        thismiles = request.form["miles"]
        thisstats = request.form["stats"]
        thisminutes = request.form["minutes"]
        newfit = Fitness(date=thisdate, summary=thissummary, type_id=thistype_id, miles=thismiles, stats=thisstats,
                         minutes=thisminutes)
        newfit.users.clear()
        thisuser = request.form.getlist("username")
        for user in thisuser:
            user = User.query.filter_by(username=user).first()
            newfit.users.append(user)
        if thisstory and thisstory != "None":
            newstory = Fitstory(storydet=thisstory)
            newfit.story_fit.append(newstory)
        db.session.add(newfit)
        db.session.commit()
        return redirect('/index')
    else:
        stypes = [value for (value,) in Typefit.query.with_entities(Typefit.typedet).all()]
        users_all = [value for (value,) in User.query.with_entities(User.username).all()]
        typename = "Walk"
        return render_template('newitem.html', title='New item', today=today, stypes=stypes, typename=typename,
                               users_all=users_all, users_set=users_all[1])


@app.route('/queries', methods=["POST", "GET"])
def queries():
    if request.method == "POST":
        qname = request.form["query"]
        if qname == "top_climbs":
            items = Fitness.query.outerjoin(Fitstory).with_entities(
                Fitness.id, Fitness.date,
                Fitness.summary, Fitness.miles, Fitness.stats,
                Fitness.minutes,
                Fitstory.storydet).filter(Fitness.type_id == 5).order_by(desc(Fitness.stats)).limit(10).all()
            return render_template('queries.html', title=qname, items=items)
        elif qname == "longest_walks":
            items = Fitness.query.outerjoin(Fitstory).with_entities(
                Fitness.id, Fitness.date,
                Fitness.summary, Fitness.miles, Fitness.stats,
                Fitness.minutes,
                Fitstory.storydet).filter(Fitness.type_id == 5).order_by(desc(Fitness.miles)).limit(10).all()
            return render_template('queries.html', title=qname, items=items)
        elif qname == "miles_walked_per_year":
            milesh = Fitness.query.with_entities(
                func.year(Fitness.date).label("year"),
                func.sum(Fitness.miles).label("miles")).filter(
                Fitness.users.any(User.id == 2),
                Fitness.type_id == 5).group_by(func.year(Fitness.date)).all()
            milesd = Fitness.query.with_entities(
                func.year(Fitness.date).label("year"),
                func.sum(Fitness.miles).label("miles")).filter(
                Fitness.users.any(User.id == 1),
                Fitness.type_id == 5).group_by(func.year(Fitness.date)).all()
            totalh = Fitness.query.with_entities(func.sum(Fitness.miles).label("miles")).filter(
                Fitness.users.any(User.id == 2), Fitness.type_id == 5).first()
            totald = Fitness.query.with_entities(func.sum(Fitness.miles).label("miles")).filter(
                Fitness.users.any(User.id == 1), Fitness.type_id == 5).first()
            return render_template('querym.html', title=qname, milesh=milesh, milesd=milesd, totalh=totalh,
                                   totald=totald)
        elif qname == "fastest_runs":
            items = Fitness.query.outerjoin(Fitstory).with_entities(
                Fitness.id, Fitness.date,
                Fitness.summary, Fitness.miles, Fitness.stats,
                Fitness.minutes,
                Fitstory.storydet).filter(Fitness.type_id == 3).order_by(Fitness.minutes).limit(10).all()
            return render_template('queries.html', title=qname, items=items)
        else:
            qname = "No valid query selected"
            items = []
            return render_template('queries.html', title=qname, items=items)
    else:
        items = Fitness.query.join(Typefit).outerjoin(Fitstory).with_entities(
            Fitness.id, Fitness.date,
            Typefit.typedet, Fitness.summary,
            Fitness.miles, Fitness.stats,
            Fitness.minutes,
            Fitstory.storydet).filter(
            Fitness.type_id == 5).order_by(desc(Fitness.date)).limit(50).all()
        return render_template('queries.html', title="all walks", items=items)


@app.route('/recentstats', methods=["POST", "GET"])
def recentstats():
    yearago = datetime.date.today() - relativedelta(years=1)
    monthago = datetime.date.today() - relativedelta(months=1)
    month3ago = datetime.date.today() - relativedelta(months=3)
    weekago = datetime.date.today() - relativedelta(weeks=1)
    yearstart = datetime.date(datetime.date.today().year, 1, 1)
    daysytd = (datetime.date.today() - yearstart).days
    if request.method == "POST":
        qname = request.form["query"]
        if qname == "walks":
            fit_query_type = 5
        elif qname == "alcohol":
            fit_query_type = 9
        elif qname == "runs":
            fit_query_type = 3
        elif qname == "walksandruns":
            fit_query_type = 99
        else:
            qname = "No valid query selected"
            return render_template('recentstats.html', title=qname)
    else:
        qname = "walks"
        fit_query_type = 5
    heztoty = get_total(2, yearago, fit_query_type)
    heztotm3 = get_total(2, month3ago, fit_query_type)
    heztotm = get_total(2, monthago, fit_query_type)
    heztotw = get_total(2, weekago, fit_query_type)
    heztotytd = get_total(2, yearstart, fit_query_type)
    deetoty = get_total(1, yearago, fit_query_type)
    deetotm3 = get_total(1, month3ago, fit_query_type)
    deetotm = get_total(1, monthago, fit_query_type)
    deetotw = get_total(1, weekago, fit_query_type)
    deetotytd = get_total(1, yearstart, fit_query_type)
    hezpwy = round(heztoty / 52, 2) if heztoty else 0.00
    hezpwm3 = round(heztotm3 * 4 / 52, 2) if heztotm3 else 0.00
    hezpwm = round(heztotm * 12 / 52, 2) if heztotm else 0.00
    hezpwytd = round(heztotytd * 7 / daysytd, 2) if heztotytd else 0.00
    deepwy = round(deetoty / 52, 2) if deetoty else 0.00
    deepwm3 = round(deetotm3 * 4 / 52, 2) if deetotm3 else 0.00
    deepwm = round(deetotm * 12 / 52, 2) if deetotm else 0.00
    deepwytd = round(deetotytd * 7 / daysytd, 2) if deetotytd else 0.00
    return render_template('recentstats.html', title=qname, heztoty=heztoty, heztotm3=heztotm3, heztotm=heztotm,
                           heztotw=heztotw, heztotytd=heztotytd, hezpwy=hezpwy, hezpwm3=hezpwm3, hezpwm=hezpwm,
                           hezpwytd=hezpwytd,
                           deetoty=deetoty, deetotm3=deetotm3, deetotm=deetotm, deetotw=deetotw, deetotytd=deetotytd,
                           deepwy=deepwy,
                           deepwm3=deepwm3, deepwm=deepwm, deepwytd=deepwytd)


def get_total(User_Id, Start_Date, Fit_Id):
    User_Id = User_Id
    Start_Date = Start_Date
    Fit_Id = Fit_Id
    if Fit_Id == 9:
        total = Fitness.query.with_entities(func.sum(Fitness.stats).label("units")).filter(
            Fitness.users.any(User.id == User_Id), Fitness.date >= Start_Date, Fitness.type_id == Fit_Id).first()[0]
    elif Fit_Id == 99:
        total = Fitness.query.with_entities(func.sum(Fitness.miles)).filter(
            Fitness.users.any(User.id == User_Id), Fitness.date >= Start_Date,
            or_(Fitness.type_id == 3, Fitness.type_id == 5)).first()[0]
    else:
        total = Fitness.query.with_entities(func.sum(Fitness.miles)).filter(
            Fitness.users.any(User.id == User_Id), Fitness.date >= Start_Date, Fitness.type_id == Fit_Id).first()[0]
    return total


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('signin/register.html', title='Register', form=form)


def replace_users(dictum, key_to_find, definition):
    for key in dictum.keys():
        if key == key_to_find:
            current_dict[key] = definition


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('signin/reset_password_request.html', title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('signin/reset_password.html', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    return render_template('signin/user.html', user=user)
