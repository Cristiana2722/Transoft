from transoft.app.functions import get_order_info, get_invoice_info
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
import pdfplumber
from datetime import datetime, timedelta
from transoft.app.extensions import mongo
from bson.objectid import ObjectId
from transoft.app.forms.uploadform import UploadedOrderForm, UploadedInvoiceForm

upload_routes_blueprint = Blueprint('upload_routes', __name__)


@upload_routes_blueprint.route('/upload', methods=['GET', 'POST'])
def upload_file():
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să încarci fișiere.", "warning")
        return redirect(url_for('user_routes.login'))

    forms_order = []
    forms_invoice = []
    doc_type = None

    if request.method == 'POST':
        pdf_file = request.files.get('pdf_file')
        doc_type = request.form.get('doc_type')

        if not pdf_file or pdf_file.filename == '':
            flash('Selectează un fișier PDF valid.', 'danger')
            return render_template('upload.html', forms_order=forms_order, forms_invoice=forms_invoice,
                                   doc_type=doc_type)

        if not pdf_file.filename.lower().endswith('.pdf'):
            flash('Doar fișiere PDF sunt acceptate.', 'danger')
            return render_template('upload.html', forms_order=forms_order, forms_invoice=forms_invoice,
                                   doc_type=doc_type)

        with pdfplumber.open(pdf_file) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)

        if doc_type == 'order':
            parsed_data = get_order_info(text)
            if not parsed_data:
                flash('PDF greșit. Verifică tipul de fișier selectat!', 'danger')
            else:
                for idx, data in enumerate(parsed_data):
                    if "order_date" in data and isinstance(data["order_date"], str):
                        try:
                            data["order_date"] = datetime.strptime(data["order_date"], "%d.%m.%Y").date()
                        except ValueError:
                            data["order_date"] = None
                    form = UploadedOrderForm(data=data, prefix=str(idx))
                    forms_order.append(form)

        elif doc_type == 'invoice':
            parsed_data = get_invoice_info(text)
            if not parsed_data:
                flash('PDF greșit. Verifică tipul de fișier selectat!', 'danger')
            else:
                if "invoice_date" in parsed_data and isinstance(parsed_data["invoice_date"], str):
                    try:
                        parsed_data["invoice_date"] = datetime.strptime(parsed_data["invoice_date"], "%d.%m.%Y").date()
                    except ValueError:
                        parsed_data["invoice_date"] = None
                form = UploadedInvoiceForm(data=parsed_data)
                forms_invoice.append(form)
        else:
            flash('Tip fișier necunoscut.', 'danger')

    return render_template('upload.html', forms_order=forms_order, forms_invoice=forms_invoice, doc_type=doc_type)


@upload_routes_blueprint.route('/upload/orders', methods=['POST'])
def upload_order():
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să adaugi proforme.", "warning")
        return redirect(url_for('user_routes.login'))

    try:
        order_count = int(request.form.get("order_count", 0))
    except ValueError:
        order_count = 0

    inserted = 0
    for i in range(order_count):
        form = UploadedOrderForm(request.form, prefix=str(i))
        if form.validate():
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
                "vehicle": form.vehicle.data,
                "trailer": form.trailer.data,
                "amount": float(form.amount.data) if form.amount.data else 0.0,
                "departure": form.departure.data,
                "arrival": form.arrival.data,
                "distance": float(form.distance.data) if form.distance.data else 0.0
            })
            inserted += 1

    flash(f"{inserted} referințe salvate cu succes!", "success")
    return redirect(url_for('orders_routes.orders'))


@upload_routes_blueprint.route('/upload/invoice', methods=['POST'])
def upload_invoice():
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să adaugi facturi.", "warning")
        return redirect(url_for('user_routes.login'))

    form = UploadedInvoiceForm(request.form)
    if not form.validate():
        flash("Formularul facturii este invalid.", "danger")
        return redirect(url_for('upload_routes.upload_file'))

    position = form.position.data
    invoice_no = form.invoice_no.data
    invoice_date = form.invoice_date.data
    freight_value = float(form.freight_value.data) if form.freight_value.data else 0.0

    order = mongo.db.orders.find_one({
        "user_id": ObjectId(user_id),
        "position": position
    })

    if not order:
        flash(f"Nu există o comandă cu referința '{position}' pentru a atașa factura.", "danger")
        return redirect(url_for('upload_routes.upload_file'))

    mongo.db.orders.update_one(
        {"_id": order["_id"]},
        {"$set": {
            "invoice_no": invoice_no,
            "invoice_date": datetime.combine(invoice_date, datetime.min.time()),
            "freight_value": freight_value
        }}
    )

    mongo.db.receivings.insert_one({
        "user_id": ObjectId(user_id),
        "receiving_type": "Factură",
        "description": invoice_no,
        "amount": freight_value,
        "issue_date": datetime.combine(invoice_date, datetime.min.time()),
        "due_date": datetime.combine(invoice_date, datetime.min.time()) + timedelta(days=28),
        "received": False
    })

    flash(f"Factura a fost atașată comenzii {position}!", "success")
    return redirect(url_for('orders_routes.orders'))
