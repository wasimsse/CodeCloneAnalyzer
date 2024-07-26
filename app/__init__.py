from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO()

def create_app():
    app = Flask(__name__)
    app.config.from_object('config.Config')

    with app.app_context():
        from . import routes
        app.register_blueprint(routes.bp)

    socketio.init_app(app)
    return app
