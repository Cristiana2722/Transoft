import datetime
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from transoft.app.forms.fuelsform import FuelForm, EditFuelForm
from transoft.app.extensions import mongo
from bson.objectid import ObjectId

fuels_routes_blueprint = Blueprint('fuels_routes', __name__)


@fuels_routes_blueprint.route('/fuels')
def fuels():
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să vezi alimentările.", "warning")
        return redirect(url_for("user_routes.login"))

    search_plate = request.args.get('plate_number', '').strip()

    query = {"user_id": ObjectId(user_id)}
    if search_plate:
        query["plate_number"] = {"$regex": search_plate, "$options": "i"}

    fuels_cursor = mongo.db.fuels.find(query)
    fuels = list(fuels_cursor)

    fuels.sort(key=lambda f: (f.get('plate_number', ''), f.get('fuel_date', datetime.min)))

    previous_data = {}
    for fuel in fuels:
        plate = fuel.get('plate_number')
        current_km = fuel.get('km', 0) or 0
        current_diesel = fuel.get('diesel', 0) or 0
        current_adblue = fuel.get('adblue', 0) or 0

        fuel['distance'] = '-'
        fuel['diesel_consumption'] = '-'
        fuel['adblue_consumption'] = '-'

        if plate in previous_data:
            previous_km = previous_data[plate]
            if previous_km > 0:
                distance = current_km - previous_km
                if distance > 0:
                    fuel['distance'] = distance
                    fuel['diesel_consumption'] = round((current_diesel / distance) * 100, 2)
                    fuel['adblue_consumption'] = round((current_adblue / distance) * 100, 2)

        previous_data[plate] = current_km

    return render_template('fuels.html', fuels=fuels, search_plate=search_plate)


@fuels_routes_blueprint.route('/fuels/add', methods=['GET', 'POST'])
def add_fuel():
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să adaugi alimentări.", "warning")
        return redirect(url_for('user_routes.login'))

    form = FuelForm()

    if form.validate_on_submit():
        mongo.db.fuels.insert_one({
            "user_id": ObjectId(user_id),
            "plate_number": form.plate_number.data.upper(),
            "fuel_date": datetime.combine(form.fuel_date.data, datetime.min.time()),
            "km": form.km.data,
            "diesel": float(form.diesel.data),
            "adblue": float(form.adblue.data),
        })
        flash("Alimentarea a fost adăugată cu succes!", "success")
        return redirect(url_for('fuels_routes.fuels'))

    return render_template('add_fuel.html', form=form)


@fuels_routes_blueprint.route('/fuels/<fuel_id>/edit', methods=['GET', 'POST'])
def edit_fuel(fuel_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să modifici alimentări.", "warning")
        return redirect(url_for('user_routes.login'))

    fuel = mongo.db.fuels.find_one({"_id": ObjectId(fuel_id), "user_id": ObjectId(user_id)})
    if not fuel:
        flash("Alimentarea nu a fost găsită.", "danger")
        return redirect(url_for('fuels_routes.fuels'))

    form = EditFuelForm(obj=fuel)

    if form.validate_on_submit():
        mongo.db.fuels.update_one(
            {"_id": ObjectId(fuel_id)},
            {"$set": {
                "plate_number": form.plate_number.data.upper(),
                "fuel_date": datetime.combine(form.fuel_date.data, datetime.min.time()),
                "km": form.km.data,
                "diesel": float(form.diesel.data),
                "adblue": float(form.adblue.data),
            }}
        )
        flash("Alimentarea a fost actualizată cu succes!", "success")
        return redirect(url_for('fuels_routes.fuels'))

    if request.method == "GET":
        form.plate_number.data = fuel.get("plate_number")
        form.fuel_date.data = fuel.get("fuel_date").date() if isinstance(fuel.get("fuel_date"), datetime) else None
        form.km.data = fuel.get("km")
        form.diesel.data = fuel.get("diesel")
        form.adblue.data = fuel.get("adblue")

    return render_template('edit_fuel.html', form=form, fuel=fuel)


@fuels_routes_blueprint.route('/fuels/<fuel_id>/delete', methods=['POST'])
def delete_fuel(fuel_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("Trebuie să fii logat ca să ștergi alimentări.", "warning")
        return redirect(url_for('user_routes.login'))

    result = mongo.db.fuels.delete_one({
        "_id": ObjectId(fuel_id),
        "user_id": ObjectId(user_id)
    })

    if result.deleted_count == 1:
        flash("Alimentarea a fost ștearsă cu succes!", "success")
    else:
        flash("Alimentarea nu a fost găsită sau nu ai dreptul să o ștergi.", "danger")

    return redirect(url_for('fuels_routes.fuels'))
