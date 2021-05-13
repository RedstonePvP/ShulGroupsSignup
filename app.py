from flask import Flask, render_template, session, redirect, url_for, abort, request, flash
from forms import *
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
import datetime
import json
import re


app = Flask(__name__)
app.secret_key = json.load(open("config.json"))["secret-key"]
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///site.db"
db = SQLAlchemy(app)

pass_salt = "ugy4+0W93FJLOS(*$&Th.;s;o"
admin_user = "username"
admin_pass = "password"
ALLGROUP = 2

urlconf = re.compile(
        r'^(?:http|ftp)s?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' #domain...
        r'localhost|' #localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)


class Week(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False)
    active = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)


class Groups(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    total = db.Column(db.Integer, nullable=False)


class ActiveGroups(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    week_id = db.Column(db.Integer, nullable=False)
    group_id = db.Column(db.Integer, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    filled = db.Column(db.Integer, nullable=False)
    url = db.Column(db.String(500))


class Reservations(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, nullable=False)
    week_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    email = db.Column(db.String(100), nullable=False)
    addr = db.Column(db.String(100), nullable=False)
    parent_name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(100), nullable=False)
    pickup_name = db.Column(db.String(100), nullable=False)
    minyan = db.Column(db.String(100), nullable=False)
    alerg = db.Column(db.String(100), nullable=False)


def update_old_weeks():
    # this function is used to change any weeks that are in the past from active 1 or 2, down to 0 which is inactive
    weeks = Week.query.filter(or_(Week.active == 1, Week.active == 2)).all()
    for week in weeks:
        if week.date.date() < datetime.datetime.now().date():
            week.active = 0
    db.session.commit()
    return "done"


@app.errorhandler(500)
def iner_error():
    return render_template("reload.html")


@app.route("/")
def index_route():
    update_old_weeks()
    l_data = []
    cur_weeks = Week.query.filter_by(active=2).all()
    for week in cur_weeks:
        print(f"WEEK: {week}")
        grps = ActiveGroups.query.filter_by(week_id=week.id).all()
        w_data = []
        for grp in grps:
            print(f"GROUPS: {grp}")
            gdata = Groups.query.filter_by(id=grp.group_id).first()
            dis = "dark"
            lnk = f"/register/{week.id}/{grp.group_id}"
            if grp.total == grp.filled:
                dis = "danger"
                lnk = "#"
            if grp.url:
                lnk = grp.url
            w_data.append([gdata.name, dis, lnk])
        l_data.append([week.date.strftime("%m/%d/%y"), w_data, week.name])

    return render_template("home.html", l_data=l_data)


@app.route("/register/<week>/<grp>", methods=["GET", "POST"])
def register_route(week, grp):
    actvgrp = ActiveGroups.query.filter_by(group_id=grp, week_id=week).first()
    grp = Groups.query.filter_by(id=grp).first()
    week = Week.query.filter_by(id=week).first()
    form = RegisterForm()

    if not week:
        flash("Sorry, That group is not open right now er-1")
        return redirect(url_for("index_route"))
    if not actvgrp:
        flash("Sorry, That group is not open right now er-2")
        return redirect(url_for("index_route"))
    if not grp:
        flash("Sorry, That group is not open right now er-3")
        return redirect(url_for("index_route"))
    if actvgrp.total == actvgrp.filled:
        flash("Sorry, That group is not open right now er-4")
        return redirect(url_for("index_route"))
    if not week.active == 2:
        flash("Sorry, That group is not open right now er-5")
        return redirect(url_for("index_route"))

    if form.validate_on_submit():
        print(f"cname:{form.cname.data}, pname:{form.pname.data}")
        actvgrp.filled += 1
        newRes = Reservations(group_id=grp.id, week_id=week.id, name=form.cname.data, parent_name=form.pname.data,
                              age=int(form.age.data), email=form.email.data, addr=form.addr.data, phone=form.phone.data,
                              pickup_name=form.pickup.data, minyan=form.minyan.data, alerg=form.alerg.data)
        db.session.add(newRes)
        db.session.commit()
        res = Reservations.query.filter_by(name=form.cname.data, group_id=grp.id, week_id=week.id, addr=form.addr.data).first()
        return render_template("confirm.html", date=week.date.strftime('%m/%d/%y'), grp=grp.name,
                               child=form.cname.data, parent=form.pname.data, id=res.id)

    return render_template("register.html", form=form, title=f"{grp.name} - {week.date.strftime('%m/%d/%y')}")


@app.route("/printout/week/full/<week>")
def printout_week_full_route(week):
    if "logged_in" not in session:
        flash("You need to be logged in to do that!")
        return redirect(url_for("index_route"))
    week = Week.query.filter_by(id=week).first()
    print(week.id)
    grps = ActiveGroups.query.filter_by(week_id=week.id).all()
    l_data = []
    for grp in grps:
        print(f"group! {grp.id}")
        grpn = Groups.query.filter_by(id=grp.group_id).first()
        g_data = [grpn.name, []]
        kids = Reservations.query.filter_by(group_id=grpn.id, week_id=week.id).all()
        for kid in kids:
            g_data[1].append([kid.name, kid.parent_name, kid.id, kid.email, kid.addr, kid.phone, kid.pickup_name,
                              kid.minyan, kid.alerg])
        l_data.append(g_data)
    print(l_data)
    return render_template("print_week_full.html", l_data=l_data, date=week.date.strftime('%m/%d/%y'))


@app.route("/printout/week/door/<week>")
def printout_week_door_route(week):
    if "logged_in" not in session:
        flash("You need to be logged in to do that!")
        return redirect(url_for("index_route"))
    week = Week.query.filter_by(id=week).first()
    print(week.id)
    grps = ActiveGroups.query.filter_by(week_id=week.id).all()
    l_data = []
    for grp in grps:
        print(f"group! {grp.id}")
        grpn = Groups.query.filter_by(id=grp.group_id).first()
        g_data = [grpn.name, []]
        kids = Reservations.query.filter_by(group_id=grpn.id, week_id=week.id).all()
        for kid in kids:
            g_data[1].append([kid.name, kid.pickup_name, kid.minyan, kid.id])
        l_data.append(g_data)
    print(l_data)
    return render_template("print_week_door.html", l_data=l_data, date=week.date.strftime('%m/%d/%y'))


@app.route("/login", methods=["GET", "POST"])
def login_route():
    form = LoginForm()
    if "logged_in" in session:
        flash("you are already logged in!")
        return redirect(url_for("index_route"))

    if form.validate_on_submit():
        if form.username.data == admin_user and form.password.data == admin_pass:
            session["logged_in"] = True
            flash("You are logged in")
            return redirect(url_for("admin_route"))
        else:
            flash("Sorry, username or password is invalid. Please try again")

    return render_template("login.html", form=form)


@app.route("/logout")
def logout_route():
    session.clear()
    return redirect(url_for("index_route"))


@app.route("/testing")
def testing_route():

    return render_template("week_printout.html")


@app.route("/admin")
def admin_route():
    update_old_weeks()
    if "logged_in" not in session:
        flash("You need to be logged in to do that!")
        return redirect(url_for("index_route"))

    return render_template("admin_home.html")


@app.route("/admin/manage/weeks")
def admin_weeks_manage():
    update_old_weeks()
    if "logged_in" not in session:
        flash("You need to be logged in to do that!")
        return redirect(url_for("index_route"))

    actvweeks = Week.query.filter(or_(Week.active == 1, Week.active == 2)).all()
    l_data = []
    for week in actvweeks:
        w_data = [week.id, week.date.strftime('%m/%d/%y')]
        if week.active == 2:
            w_data.append("check")
        else:
            w_data.append("times")
        l_data.append(w_data)

    return render_template("admin_week_manage.html", l_data=l_data)


@app.route("/admin/manage/weeks/swtch/<weekid>")
def admin_weeks_switch_manage(weekid):
    if "logged_in" not in session:
        flash("You need to be logged in to do that!")
        return redirect(url_for("index_route"))
    week = Week.query.filter_by(id=weekid).first()
    if week.active == 2:
        week.active = 1
    elif week.active == 1:
        week.active = 2
    db.session.commit()
    return redirect(url_for("admin_weeks_manage"))


@app.route("/admin/manage/weeks/del/<weekid>")
def admin_weeks_del_manage(weekid):
    if "logged_in" not in session:
        flash("You need to be logged in to do that!")
        return redirect(url_for("index_route"))
    week = Week.query.filter_by(id=weekid).first()
    grps = ActiveGroups.query.filter_by(week_id=week.id).all()
    reses = Reservations.query.filter_by(week_id=week.id).all()
    for res in reses:
        db.session.delete(res)
    for grp in grps:
        db.session.delete(grp)
    db.session.delete(week)
    db.session.commit()
    return redirect(url_for("admin_weeks_manage"))


@app.route("/admin/manage/week/<weekid>")
def admin_week_manage(weekid):
    if "logged_in" not in session:
        flash("You need to be logged in to do that!")
        return redirect(url_for("index_route"))

    week = Week.query.filter_by(id=weekid).first()
    agrps = ActiveGroups.query.filter_by(week_id=week.id).all()
    l_data = []

    if agrps[0].url:
        l_data.append([agrps.url, "NA", "NA", "NA", "form"])
    else:
        for grp in agrps:
            grpn = Groups.query.filter_by(id=grp.group_id).first()
            g_data = [grp.id, grpn.name, grp.total, grp.filled]
            l_data.append(g_data)

    return render_template("admin_week_groups_manage.html", l_data=l_data, title=week.date.strftime('%m/%d/%y'))


@app.route("/admin/manage/week/<grpid>/del")
def admin_week_manage_del(grpid):
    if "logged_in" not in session:
        flash("You need to be logged in to do that!")
        return redirect(url_for("index_route"))

    grps = ActiveGroups.query.filter_by(id=grpid).all()
    reses = Reservations.query.filter_by(week_id=grps.week_id, group_id=grps.group_id).all()

    for grp in grps:
        db.session.delete(grp)
    for res in reses:
        db.session.delete(res)
    db.session.commit()
    return redirect(url_for("admin_weeks_manage"))


@app.route("/admin/manage/group/<grpid>")
def admin_group_manage(grpid):
    if "logged_in" not in session:
        flash("You need to be logged in to do that!")
        return redirect(url_for("index_route"))
    grp = ActiveGroups.query.filter_by(id=grpid).first()
    kids = Reservations.query.filter_by(group_id=grp.group_id, week_id=grp.week_id).all()
    l_data = []
    for kid in kids:
        l_data.append([kid.id, kid.name, kid.parent_name, kid.email, kid.addr, kid.phone, kid.pickup_name,
                       kid.minyan, kid.alerg])

    return render_template("admin_week_ppl_manage.html", l_data=l_data)


@app.route("/admin/manage/group/<kidid>/del")
def admin_group_manage_del(kidid):
    if "logged_in" not in session:
        flash("You need to be logged in to do that!")
        return redirect(url_for("index_route"))
    kid = Reservations.query.filter_by(id=kidid)
    numr = ActiveGroups.query.filter_by(week_id=kid.week_id, group_id=kid.group_id).first()
    numr.filled -= 1
    kid.delete()
    db.session.commit()
    flash("Reservation Deleted")
    return redirect(url_for("admin_weeks_manage"))


@app.route("/admin/new/group", methods=["GET", "POST"])
def admin_new_group():
    if "logged_in" not in session:
        flash("You need to be logged in to do that!")
        return redirect(url_for("index_route"))
    form = NewGroup()

    if form.validate_on_submit():
        newGroup = Groups(name=form.name.data, total=int(form.total.data))
        db.session.add(newGroup)
        db.session.commit()
        return redirect(url_for("admin_route"))

    return render_template("admin_new_group.html", form=form)


@app.route("/admin/manage/groups/del/<grp>")
def admin_groups_del_manage(grp):
    if "logged_in" not in session:
        flash("You need to be logged in to do that!")
        return redirect(url_for("index_route"))

    grp = Groups.query.filter_by(id=grp).first()
    if not grp:
        flash("Error, group not found")
        return redirect(url_for("admin_groups_manage"))
    grp.delete()
    flash("Group Deleted")
    return redirect(url_for("admin_groups_manage"))


@app.route("/admin/manage/groups")
def admin_groups_manage():
    if "logged_in" not in session:
        flash("You need to be logged in to do that!")
        return redirect(url_for("index_route"))

    grps = Groups.query.all()
    l_data = []
    for group in grps:
        w_data = [group.id, group.name, group.total]
        l_data.append(w_data)

    return render_template("admin_group_manage.html", l_data=l_data)


@app.route("/admin/new/week", methods=["GET", "POST"])
def admin_new_week():
    if "logged_in" not in session:
        flash("You need to be logged in to do that!")
        return redirect(url_for("index_route"))
    form = NewWeek()

    form.grps.choices = []
    grps = Groups.query.all()
    for grp in grps:
        form.grps.choices.append((str(grp.id), grp.name))

    if form.validate_on_submit():
        print(f"date: {form.date.data}, groups: {form.grps.data}, is active?: {form.visible.data}")
        actv = 1
        if form.visible.data:
            actv = 2
        date = form.date.data
        dt = datetime.datetime.combine(date, datetime.datetime.min.time())
        newWeek = Week(date=dt, active=actv, name=form.name.data)
        db.session.add(newWeek)
        db.session.commit()
        weekid = Week.query.filter_by(date=dt, name=form.name.data).first()
        print(form.url.data)
        if re.match(urlconf, form.url.data):
            ActvGrp = ActiveGroups(week_id=weekid.id, group_id=ALLGROUP, total=10, filled=0, url=form.url.data)
            db.session.add(ActvGrp)
        else:
            for grp in form.grps.data:
                ttl = Groups.query.filter_by(id=int(grp)).first()
                ActvGrp = ActiveGroups(week_id=weekid.id, group_id=int(grp), total=ttl.total, filled=0, url=None)
                db.session.add(ActvGrp)
        db.session.commit()
        return redirect(url_for("admin_route"))
    
    return render_template("admin_new_week.html", form=form)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0")
