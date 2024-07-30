from flask import Flask
from flask_socketio import SocketIO

socketio = SocketIO()

def create_app():
    app = Flask(__name__, template_folder='../templates')
    app.config.from_object('config.Config')

    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    socketio.init_app(app)
    return app
