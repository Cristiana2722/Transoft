from flask import Blueprint, render_template, redirect, url_for, flash, session
from datetime import datetime
from bson import ObjectId
from bson.son import SON
from transoft.app.extensions import mongo
from transoft.app.forms.userform import UserForm, AdminEditAccountForm
from werkzeug.security import generate_password_hash

routes_blueprint = Blueprint('routes', __name__)


@routes_blueprint.route('/')
def login():
    return redirect(url_for('user_routes.login'))


@routes_blueprint.route('/home')
def home():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for("user_routes.login"))
    else:
        user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    now = datetime.utcnow()
    current_year = now.year

    receivings_agg = mongo.db.receivings.aggregate([
        {"$match": {"user_id": ObjectId(user_id), "issue_date": {"$gte": datetime(current_year,1,1)}}},
        {"$group": {
            "_id": {"month": {"$month": "$issue_date"}},
            "total": {"$sum": "$amount"}
        }},
        {"$sort": SON([("_id.month", 1)])}
    ])
    receivings_per_month = [0]*12
    for r in receivings_agg:
        receivings_per_month[r['_id']['month']-1] = r['total']

    payments_agg = mongo.db.payments.aggregate([
        {"$match": {"user_id": ObjectId(user_id), "issue_date": {"$gte": datetime(current_year,1,1)}}},
        {"$group": {
            "_id": {"month": {"$month": "$issue_date"}},
            "total": {"$sum": "$amount"}
        }},
        {"$sort": SON([("_id.month", 1)])}
    ])
    payments_per_month = [0]*12
    for p in payments_agg:
        payments_per_month[p['_id']['month']-1] = p['total']

    return render_template('index.html', user=user, receivings_per_month=receivings_per_month, payments_per_month=payments_per_month)


@routes_blueprint.route('/dashboard', methods=["GET"])
def dashboard():
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat pentru a accesa pagina admin-ului.", "warning")
        return redirect(url_for('user_routes.login'))

    user = mongo.db.users.find_one({"_id": ObjectId(user_id)})

    stats = mongo.db.command("collstats", "orders")
    used_bytes = stats.get('size', 0)
    max_bytes = 512 * 1024 * 1024 # 512 MB
    used_percent = round((used_bytes / max_bytes) * 100, 2)
    free_percent = 100 - used_percent

    create_form = UserForm()
    edit_form = AdminEditAccountForm()

    return render_template(
        'dashboard.html',
        user=user,
        used_bytes=used_bytes,
        max_bytes=max_bytes,
        used_percent=used_percent,
        free_percent=free_percent,
        create_form=create_form,
        edit_form=edit_form
    )


@routes_blueprint.route('/create_user', methods=["POST"])
def create_user():
    form = UserForm()
    if form.validate_on_submit():
        existing_username = mongo.db.users.find_one({
            "username": {"$regex": f"^{form.username.data}$", "$options": "i"}
        })

        if existing_username:
            flash('Username deja existent!', 'danger')
        else:
            new_user = {
                "username": form.username.data,
                "password_hash": generate_password_hash(form.password.data)
            }
            mongo.db.users.insert_one(new_user)
            flash('Contul a fost creat cu succes!', 'success')

    return redirect(url_for('routes.dashboard'))


@routes_blueprint.route('/edit_account', methods=["POST"])
def edit_account():
    form = AdminEditAccountForm()
    if form.validate_on_submit():
        target_user = mongo.db.users.find_one({"username": form.username.data})
        if not target_user:
            flash(f"User '{form.username.data}' not found.", "danger")
            return redirect(url_for('routes.dashboard'))

        if form.password.data:
            mongo.db.users.update_one(
                {"_id": target_user["_id"]},
                {"$set": {"password_hash": generate_password_hash(form.password.data)}}
            )
            flash(f"Parola pentru '{form.username.data}' a fost actualizată cu succes!", "success")
        else:
            flash("Nu a fost introdusă nicio parolă nouă.", "warning")

    return redirect(url_for('routes.dashboard'))
