import sqlalchemy
from flask import render_template, redirect, url_for, request
from flask_login import login_required
from app import db
from app.main import bp
import datetime
from dateutil.relativedelta import relativedelta
from sqlalchemy import asc, desc, extract, func, literal, and_, or_
from app.models import Fitness, Fitstory, Typefit, User, user_fit


@bp.route('/deleteitem/<int:id>')
def deleteitem(id):
    delete_item = Fitness.query.get(id)
    delete_story = Fitstory.query.filter(Fitstory.fit_id == id).one_or_none()
    if delete_story is not None:
        db.session.delete(delete_story)
    db.session.delete(delete_item)
    db.session.commit()

    return redirect(url_for('main.index'))


@bp.route('/fit_item/<int:id>', methods=["POST", "GET"])
def fit_item(id):
    action = request.args.get('action', "view", type=str)
    if request.method == "POST":
        post_item(id, action)
        return redirect(url_for('main.index'))
    item, typename, stypes, users_all, users_set = getitemvalues(id, action)

    return render_template('fit_item.html', action=action, item=item, stypes=stypes,
                           today=datetime.date.today(), typename=typename, users_all=users_all, users_set=users_set)


def getitemvalues(id, action):
    stypes = [value for (value,) in Typefit.query.with_entities(Typefit.typedet).all()]
    users_all = [value for (value,) in User.query.with_entities(User.username).order_by(User.username).all()]
    if action == "clone" or action == "edit":
        item = \
            Fitness.query.join(Typefit).outerjoin(Fitstory).with_entities(Fitness.id, Fitness.date, Typefit.typedet,
                              Fitness.summary, Fitness.miles, Fitness.stats, Fitness.minutes, Fitstory.storydet) \
            .filter(Fitness.id == id).one_or_none()
        users_set = [value for (value,) in User.query.join(user_fit).join(Fitness).with_entities(User.username) \
                    .filter(Fitness.id == id).all()]
        typename = item.typedet
    elif action == "new":
        item = {
            'id': 0,
            'miles': "0.00",
            'minutes': "0.00",
            'stats': "0.00"
        }
        users_set = users_all[1]
        typename = stypes[4]
    else:
        raise ValueError("getvalues(): Unrecognised value for 'action' (\"{}\")".format(action))

    return item, typename, stypes, users_all, users_set


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


@bp.route('/', methods=['GET', 'POST'])
@bp.route('/index', methods=['GET', 'POST'])
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


def post_item(id, action):
    if action == "edit":
        item = Fitness.query.get(id)
        story = Fitstory.query.filter(Fitstory.fit_id == id).one_or_none()
        if story is None:
            story = Fitstory()
    else:
        item = Fitness()
        story = Fitstory()
    item.date = request.form["itemdate"]
    type = request.form["stype"]
    item.type_id = Typefit.query.with_entities(Typefit.id).filter(Typefit.typedet == type).one_or_none()[0]
    item.summary = request.form["summary"]
    item.miles = request.form["miles"]
    item.stats = request.form["stats"]
    item.minutes = request.form["minutes"]
    storydet = request.form["storydet"]
    item.users.clear()
    users_set = request.form.getlist("username")
    for user in users_set:
        user = User.query.filter_by(username=user).one_or_none()
        item.users.append(user)
    if storydet and storydet != "None":
        story.storydet = storydet
        if not type == "edit":
            item.story_fit.append(story)
    db.session.add(item)
    db.session.commit()


@bp.route('/queries', methods=["POST", "GET"])
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


@bp.route('/recentstats', methods=["POST", "GET"])
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
