from flask import Blueprint, render_template, flash, redirect, url_for, session
from transoft.app.forms.userform import UserForm, LoginForm, AccountForm, EditAccountForm, ChangePasswordForm
from transoft.app.extensions import mongo
from werkzeug.security import generate_password_hash, check_password_hash

user_routes_blueprint = Blueprint('user_routes', __name__)


@user_routes_blueprint.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = mongo.db.users.find_one({
            "username": {"$regex": f"^{form.username.data}$", "$options": "i"}
        })
        if user and check_password_hash(user['password_hash'], form.password.data):
            session['user_id'] = str(user['_id'])
            flash('Te-ai conectat cu succes!', 'success')

            if user['username'].lower() == 'admin':
                return redirect(url_for('routes.dashboard'))
            else:
                return redirect(url_for('routes.home'))

        else:
            flash('Username sau parolă greșite!', 'danger')
    return render_template('login.html', form=form)


@user_routes_blueprint.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Te-ai deconectat cu succes.', 'info')
    return redirect(url_for('routes.login'))