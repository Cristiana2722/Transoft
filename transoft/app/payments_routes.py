import datetime
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from transoft.app.forms.paymentsform import PaymentForm, EditPaymentForm
from transoft.app.extensions import mongo
from bson.objectid import ObjectId

payments_routes_blueprint = Blueprint('payments_routes', __name__)


@payments_routes_blueprint.route('/payments')
def payments():
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să vezi plățile.", "warning")
        return redirect(url_for("user_routes.login"))

    payments_cursor = mongo.db.payments.find({"user_id": ObjectId(user_id)})
    payments = list(payments_cursor)

    now = datetime.utcnow()

    for payment in payments:
        invalid_date = False

        due_date = payment.get('due_date')
        if isinstance(due_date, str):
            try:
                due_date = datetime.fromisoformat(due_date)
            except ValueError:
                due_date = None
                invalid_date = True
        elif not isinstance(due_date, datetime):
            due_date = None
            if due_date is None:
                invalid_date = True
        payment['due_date'] = due_date

        if due_date:
            payment['days_left'] = (due_date - now).days
        else:
            payment['days_left'] = None

        issue_date = payment.get('issue_date')
        if isinstance(issue_date, str):
            try:
                issue_date = datetime.fromisoformat(issue_date)
            except ValueError:
                issue_date = None
                invalid_date = True
        elif not isinstance(issue_date, datetime):
            issue_date = None
            invalid_date = True
        payment['issue_date'] = issue_date

        days_left = payment['days_left']
        if invalid_date:
            payment['row_class'] = 'bg-orange'
        elif payment.get('paid') is True:
            payment['days_left'] = '-'
            payment['row_class'] = 'bg-success'
        else:
            if days_left is None:
                payment['row_class'] = ''
            elif 3 >= days_left > 0:
                payment['row_class'] = 'bg-warning'
            elif days_left <= 0:
                payment['row_class'] = 'bg-danger'
            else:
                payment['row_class'] = ''

    def sort_key(p):
        if p['row_class'] == 'bg-orange':
            return (-1, 0)
        if p['days_left'] == '-':
            return (1, -(p['issue_date'].timestamp() if p['issue_date'] else 0))
        elif isinstance(p['days_left'], int):
            return (0, p['days_left'])
        else:
            return (0, 999999)

    payments.sort(key=sort_key)

    return render_template('payments.html', payments=payments)



@payments_routes_blueprint.route('/payments/add', methods=['GET', 'POST'])
def add_payment():
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să adaugi plăți.", "warning")
        return redirect(url_for('user_routes.login'))

    form = PaymentForm()

    from datetime import datetime

    if form.validate_on_submit():
        issue_dt = datetime.combine(form.issue_date.data, datetime.min.time())
        due_dt = datetime.combine(form.due_date.data, datetime.min.time())

        mongo.db.payments.insert_one({
            "user_id": ObjectId(user_id),
            "payment_type": form.payment_type.data,
            "description": form.description.data,
            "amount": float(form.amount.data),
            "issue_date": issue_dt,
            "due_date": due_dt,
            "paid": False
        })
        flash("Plata a fost adăugată cu succes!", "success")
        return redirect(url_for('payments_routes.payments'))
    else:
        if form.due_date.errors:
            flash(form.due_date.errors[0], "danger")

    return render_template('add_payment.html', form=form)


@payments_routes_blueprint.route('/payments/<payment_id>/edit', methods=['GET', 'POST'])
def edit_payment(payment_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să modifici plăți.", "warning")
        return redirect(url_for('user_routes.login'))

    payment = mongo.db.payments.find_one({"_id": ObjectId(payment_id), "user_id": ObjectId(user_id)})
    if not payment:
        flash("Payment not found.", "danger")
        return redirect(url_for('payments_routes.payments'))

    form = EditPaymentForm(obj=payment)

    if form.validate_on_submit():
        mongo.db.payments.update_one(
            {"_id": ObjectId(payment_id)},
            {"$set": {
                "payment_type": form.payment_type.data,
                "description": form.description.data,
                "amount": float(form.amount.data),
                "issue_date": datetime.combine(form.issue_date.data, datetime.min.time()),
                "due_date": datetime.combine(form.due_date.data, datetime.min.time()),
                "received": False
            }}
        )
        flash("Plata a fost actualizată cu succes!", "success")
        return redirect(url_for('payments_routes.payments'))
    else:
        if form.due_date.errors:
            flash(form.due_date.errors[0], "danger")

    if request.method == "GET":
        form.payment_type.data = payment.get("payment_type")
        form.description.data = payment.get("description")
        form.amount.data = payment.get("amount")
        form.issue_date.data = payment.get("issue_date").date() if payment.get("issue_date") else None
        form.due_date.data = payment.get("due_date").date() if payment.get("due_date") else None

    return render_template('edit_payment.html', form=form, payment=payment)


@payments_routes_blueprint.route('/payments/<payment_id>/delete', methods=['POST'])
def delete_payment(payment_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să ștergi plăți.", "warning")
        return redirect(url_for('user_routes.login'))

    result = mongo.db.payments.delete_one({
        "_id": ObjectId(payment_id),
        "user_id": ObjectId(user_id)
    })

    if result.deleted_count == 1:
        flash("Plata a fost ștearsă cu succes!", "success")
    else:
        flash("Plata nu a fost găsită sau nu ai dreptul să o ștergi.", "danger")

    return redirect(url_for('payments_routes.payments'))


@payments_routes_blueprint.route('/payments/toggle/<payment_id>')
def toggle_payment_status(payment_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii autentificat pentru a modifica plăți.", "warning")
        return redirect(url_for('user_routes.login'))

    payment = mongo.db.payments.find_one({
        "_id": ObjectId(payment_id),
        "user_id": ObjectId(user_id)
    })
    if not payment:
        flash("Plata nu a fost găsită.", "danger")
        return redirect(url_for('payments_routes.payments'))

    if payment.get("paid") is True:
        mongo.db.payments.update_one(
            {"_id": ObjectId(payment_id)},
            {"$set": {"paid": False}}
        )
    else:
        mongo.db.payments.update_one(
            {"_id": ObjectId(payment_id)},
            {"$set": {"paid": True}}
        )

    flash("Statusul plății a fost modificat.", "success")
    return redirect(url_for('payments_routes.payments'))
