import datetime
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from transoft.app.forms.receivingform import ReceivingForm, EditReceivingForm
from transoft.app.extensions import mongo
from bson.objectid import ObjectId

receivings_routes_blueprint = Blueprint('receivings_routes', __name__)


@receivings_routes_blueprint.route('/receivings')
def receivings():
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să vezi încasările.", "warning")
        return redirect(url_for("user_routes.login"))

    receivings_cursor = mongo.db.receivings.find({"user_id": ObjectId(user_id)})
    receivings = list(receivings_cursor)

    now = datetime.utcnow()

    for receiving in receivings:
        invalid_date = False

        due_date = receiving.get('due_date')
        if isinstance(due_date, str):
            try:
                due_date = datetime.fromisoformat(due_date)
            except ValueError:
                due_date = None
                invalid_date = True
        elif not isinstance(due_date, datetime):
            due_date = None
            invalid_date = True
        receiving['due_date'] = due_date

        if due_date:
            receiving['days_left'] = (due_date - now).days
        else:
            receiving['days_left'] = None

        issue_date = receiving.get('issue_date')
        if isinstance(issue_date, str):
            try:
                issue_date = datetime.fromisoformat(issue_date)
            except ValueError:
                issue_date = None
                invalid_date = True
        elif not isinstance(issue_date, datetime):
            issue_date = None
            invalid_date = True
        receiving['issue_date'] = issue_date

        # --- Styling logic ---
        days_left = receiving['days_left']
        if invalid_date:
            receiving['row_class'] = 'bg-orange'
        elif receiving.get('received') is True:
            receiving['days_left'] = '-'
            receiving['row_class'] = 'bg-success'
        else:
            if days_left is None or days_left > 3:
                receiving['row_class'] = ''
            elif 3 >= days_left > 0:
                receiving['row_class'] = 'bg-warning'
            elif days_left <= 0:
                receiving['row_class'] = 'bg-danger'
            else:
                receiving['row_class'] = ''

    def sort_key(r):
        if r['row_class'] == 'bg-orange':
            return (-1, 0)
        if r['days_left'] == '-':
            return (1, -(r['issue_date'].timestamp() if r['issue_date'] else 0))
        elif isinstance(r['days_left'], int):
            return (0, r['days_left'])
        else:
            return (0, 999999)

    receivings.sort(key=sort_key)

    return render_template('receivings.html', receivings=receivings)


@receivings_routes_blueprint.route('/receivings/add', methods=['GET', 'POST'])
def add_receiving():
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să adaugi încasări.", "warning")
        return redirect(url_for('user_routes.login'))

    form = ReceivingForm()

    from datetime import datetime

    if form.validate_on_submit():
        issue_dt = datetime.combine(form.issue_date.data, datetime.min.time())
        due_dt = datetime.combine(form.due_date.data, datetime.min.time())

        mongo.db.receivings.insert_one({
            "user_id": ObjectId(user_id),
            "receiving_type": form.receiving_type.data,
            "description": form.description.data,
            "amount": float(form.amount.data),
            "issue_date": issue_dt,
            "due_date": due_dt,
            "received": False
        })
        flash("Încasarea a fost adăugată cu succes!", "success")
        return redirect(url_for('receivings_routes.receivings'))
    else:
        if form.due_date.errors:
            flash(form.due_date.errors[0], "danger")

    return render_template('add_receiving.html', form=form)


@receivings_routes_blueprint.route('/receivings/<receiving_id>/edit', methods=['GET', 'POST'])
def edit_receiving(receiving_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să modifici încasări.", "warning")
        return redirect(url_for('user_routes.login'))

    receiving = mongo.db.receivings.find_one({"_id": ObjectId(receiving_id), "user_id": ObjectId(user_id)})
    if not receiving:
        flash("Încasarea nu a fost găsită.", "danger")
        return redirect(url_for('receivings_routes.receivings'))

    form = EditReceivingForm(obj=receiving)

    if form.validate_on_submit():
        mongo.db.receivings.update_one(
            {"_id": ObjectId(receiving_id)},
            {"$set": {
                "receiving_type": form.receiving_type.data,
                "description": form.description.data,
                "amount": float(form.amount.data),
                "issue_date": datetime.combine(form.issue_date.data, datetime.min.time()),
                "due_date": datetime.combine(form.due_date.data, datetime.min.time()),
                "received": False
            }}
        )
        flash("Încasarea a fost modificată cu succes!", "success")
        return redirect(url_for('receivings_routes.receivings'))
    else:
        if form.due_date.errors:
            flash(form.due_date.errors[0], "danger")

    if request.method == "GET":
        form.receiving_type.data = receiving.get("receiving_type")
        form.description.data = receiving.get("description")
        form.amount.data = receiving.get("amount")
        form.issue_date.data = receiving.get("issue_date").date() if receiving.get("issue_date") else None
        form.due_date.data = receiving.get("due_date").date() if receiving.get("due_date") else None

    return render_template('edit_receiving.html', form=form, receiving=receiving)


@receivings_routes_blueprint.route('/receivings/<receiving_id>/delete', methods=['POST'])
def delete_receiving(receiving_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să ștergi încasări.", "warning")
        return redirect(url_for('user_routes.login'))

    result = mongo.db.receivings.delete_one({
        "_id": ObjectId(receiving_id),
        "user_id": ObjectId(user_id)
    })

    if result.deleted_count == 1:
        flash("Încasarea a fost ștearsă cu succes!", "success")
    else:
        flash("Încasarea nu a fost găsită sau nu ai dreptul să o ștergi.", "danger")

    return redirect(url_for('receivings_routes.receivings'))


@receivings_routes_blueprint.route('/receivings/toggle/<receiving_id>')
def toggle_receiving_status(receiving_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii autentificat pentru a modifica încasări.", "warning")
        return redirect(url_for('user_routes.login'))

    receiving = mongo.db.receivings.find_one({
        "_id": ObjectId(receiving_id),
        "user_id": ObjectId(user_id)
    })
    if not receiving:
        flash("Încasarea nu a fost găsită.", "danger")
        return redirect(url_for('receivings_routes.receivings'))

    if receiving.get("received") is True:
        mongo.db.receivings.update_one(
            {"_id": ObjectId(receiving_id)},
            {"$set": {"received": False}}
        )
    else:
        mongo.db.receivings.update_one(
            {"_id": ObjectId(receiving_id)},
            {"$set": {"received": True}}
        )

    flash("Statusul încasării a fost modificat.", "success")
    return redirect(url_for('receivings_routes.receivings'))