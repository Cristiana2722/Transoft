import datetime
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from transoft.app.forms.ordersform import OrderForm, InvoiceForm, EditOrderForm
from transoft.app.extensions import mongo
from bson.objectid import ObjectId

orders_routes_blueprint = Blueprint('orders_routes', __name__)


@orders_routes_blueprint.route('/orders')
def orders():
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să îți vezi documentele.", "warning")
        return redirect(url_for("user_routes.login"))

    search_term = request.args.get('search', '').strip()

    query = {"user_id": ObjectId(user_id)}
    if search_term:
        query["$or"] = [
            {"position": {"$regex": search_term, "$options": "i"}},
            {"vehicle": {"$regex": search_term, "$options": "i"}}
        ]

    orders_cursor = mongo.db.orders.find(query)
    orders = list(orders_cursor)

    for order in orders:
        order['_id'] = str(order['_id'])
        order.setdefault('invoice_no', '')
        order.setdefault('freight_value', '-')
        order.setdefault('invoice_date', '')

        amount = order.get('amount')
        freight_value = order.get('freight_value')
        invoice_no = order.get('invoice_no')

        if freight_value is None and invoice_no is None or invoice_no == '':
            order['status'] = 'Factura lipsă'
            order['row_class'] = ''
        elif amount != freight_value:
            order['status'] = 'Sumă neconformă'
            order['row_class'] = 'bg-danger'
        elif invoice_no and amount == freight_value:
            order['status'] = 'OK'
            order['row_class'] = 'bg-success'
        else:
            order['status'] = 'Eroare'
            order['row_class'] = 'bg-warning'

    orders.sort(key=lambda o: o['order_date'], reverse=True)

    return render_template('orders.html', orders=orders, search_term=search_term)


@orders_routes_blueprint.route('/orders/add', methods=['GET', 'POST'])
def add_order():
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să adaugi proforme.", "warning")
        return redirect(url_for('user_routes.login'))

    form = OrderForm()

    if form.validate_on_submit():
        position = form.position.data.strip()

        existing_order = mongo.db.orders.find_one({
            "user_id": ObjectId(user_id),
            "position": position
        })

        if existing_order:
            flash(f"O proformă cu referința '{position}' există deja!", "danger")
            return redirect(url_for('orders_routes.orders'))

        mongo.db.orders.insert_one({
            "user_id": ObjectId(user_id),
            "order_date": datetime.combine(form.order_date.data, datetime.min.time()),
            "position": form.position.data,
            "vehicle": form.vehicle.data.upper(),
            "trailer": form.trailer.data.upper(),
            "amount": float(form.amount.data) if form.amount.data else 0.0,
            "departure": form.departure.data,
            "arrival": form.arrival.data,
            "distance": float(form.distance.data) if form.distance.data else 0.0
        })
        flash("Comanda a fost adăugată cu succes!", "success")
        return redirect(url_for('orders_routes.orders'))

    return render_template('add_order.html', form=form)


@orders_routes_blueprint.route('/invoices/add', methods=['GET', 'POST'])
def add_invoice():
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să adaugi facturi.", "warning")
        return redirect(url_for('user_routes.login'))

    form = InvoiceForm()

    if form.validate_on_submit():
        position = form.position.data

        order = mongo.db.orders.find_one({
            "user_id": ObjectId(user_id),
            "position": position
        })

        if not order:
            flash(f"Nu există o comandă cu referința '{position}' pentru a atașa factura.", "danger")
            return render_template('add_invoice.html', form=form)

        mongo.db.orders.update_one(
            {"_id": order["_id"]},
            {"$set": {
                "invoice_no": form.invoice_no.data,
                "invoice_date": datetime.combine(form.invoice_date.data, datetime.min.time()),
                "freight_value": float(form.freight_value.data)
            }}
        )

        mongo.db.receivings.insert_one({
            "user_id": ObjectId(user_id),
            "receiving_type": "Factură",
            "description": form.invoice_no.data,
            "amount": float(form.freight_value.data),
            "issue_date": datetime.combine(form.invoice_date.data, datetime.min.time()),
            "due_date": datetime.combine(form.invoice_date.data, datetime.min.time()) + timedelta(days=28),
            "received": False
        })

        flash(f"Factura a fost atașată cu succes comenzii nr. {order['position']}!", "success")
        return redirect(url_for('orders_routes.orders'))

    return render_template('add_invoice.html', form=form)


@orders_routes_blueprint.route('/orders/<order_id>/edit', methods=['GET', 'POST'])
def edit_order(order_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să modifici documente.", "warning")
        return redirect(url_for("user_routes.login"))

    order = mongo.db.orders.find_one({"_id": ObjectId(order_id), "user_id": ObjectId(user_id)})
    if not order:
        flash("Order not found.", "danger")
        return redirect(url_for('orders_routes.orders'))

    form = EditOrderForm()

    if form.validate_on_submit():
        set_data = {
            "order_date": datetime.combine(form.order_date.data, datetime.min.time()),
            "position": form.position.data,
            "vehicle": form.vehicle.data.upper(),
            "trailer": form.trailer.data.upper(),
            "amount": float(form.amount.data) if form.amount.data else 0.0,
            "departure": form.departure.data,
            "arrival": form.arrival.data,
            "distance": float(form.distance.data) if form.distance.data else 0.0
        }

        invoice_no = form.invoice_no.data.strip() if form.invoice_no.data else ''
        invoice_date = form.invoice_date.data
        freight_value = form.freight_value.data

        unset_data = {}

        if invoice_no:
            set_data["invoice_no"] = invoice_no
        else:
            unset_data["invoice_no"] = ""

        if invoice_date:
            set_data["invoice_date"] = datetime.combine(invoice_date, datetime.min.time())
        else:
            unset_data["invoice_date"] = ""

        if freight_value is not None and freight_value != '':
            set_data["freight_value"] = float(freight_value)
        else:
            unset_data["freight_value"] = ""

        update_query = {}
        if set_data:
            update_query["$set"] = set_data
        if unset_data:
            update_query["$unset"] = unset_data

        mongo.db.orders.update_one(
            {"_id": ObjectId(order_id)},
            update_query
        )
        flash("Documentul a fost actualizat cu succes!", "success")
        return redirect(url_for('orders_routes.orders'))

    if request.method == 'GET':
        form.order_date.data = order.get("order_date").date() if order.get("order_date") else None
        form.position.data = order.get("position")
        form.vehicle.data = order.get("vehicle")
        form.trailer.data = order.get("trailer")
        form.amount.data = order.get("amount")
        form.departure.data = order.get("departure")
        form.arrival.data = order.get("arrival")
        form.distance.data = order.get("distance")
        form.invoice_no.data = order.get("invoice_no")
        form.invoice_date.data = order.get("invoice_date").date() if order.get("invoice_date") else None
        form.freight_value.data = order.get("freight_value")

    return render_template('edit_order.html', form=form, order=order)


@orders_routes_blueprint.route('/orders/<order_id>/delete', methods=['POST'])
def delete_order(order_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să ștergi documente.", "warning")
        return redirect(url_for('user_routes.login'))

    result = mongo.db.orders.delete_one({
        "_id": ObjectId(order_id),
        "user_id": ObjectId(user_id)
    })

    if result.deleted_count == 1:
        flash("Documentul a fost șters cu succes!", "success")
    else:
        flash("Documentul nu a fost găsit sau nu ai dreptul să îl ștergi.", "danger")

    return redirect(url_for('orders_routes.orders'))
