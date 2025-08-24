import os

from flask import Flask

from transoft.app.routes import routes_blueprint
from transoft.app.user_routes import user_routes_blueprint
from transoft.app.payments_routes import payments_routes_blueprint
from transoft.app.receivings_routes import receivings_routes_blueprint
from transoft.app.fuels_routes import fuels_routes_blueprint
from transoft.app.orders_routes import orders_routes_blueprint
from transoft.app.upload_routes import upload_routes_blueprint
from flask import Flask
from transoft.app.extensions import mongo
import os
from dotenv import load_dotenv

def create_app():
    load_dotenv()
    app = Flask(__name__)
    app.config["MONGO_URI"] = os.environ.get("MONGO_URI")

    app.config['SECRET_KEY'] = 'mysecretkey777'
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    mongo.init_app(app)

    app.register_blueprint(routes_blueprint)
    app.register_blueprint(user_routes_blueprint)
    app.register_blueprint(payments_routes_blueprint)
    app.register_blueprint(receivings_routes_blueprint)
    app.register_blueprint(fuels_routes_blueprint)
    app.register_blueprint(orders_routes_blueprint)
    app.register_blueprint(upload_routes_blueprint)
    return app
