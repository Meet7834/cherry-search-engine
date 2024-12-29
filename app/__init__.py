from flask import Flask
import os


def create_app() -> Flask:
    app = Flask(__name__, template_folder=os.path.join(os.getcwd(), 'templates'))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///search_engine_data.db'

    # Initialize and register routes
    from app.models import db
    db.init_app(app)
    with app.app_context():
        db.create_all()

    from app.routes import search_api, scraper_api
    app.register_blueprint(search_api)
    app.register_blueprint(scraper_api)

    return app
