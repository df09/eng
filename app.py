from flask import Flask
from routes import bcrypt
from routes.index import index_bp
from routes.auth import auth_bp
from logger import logger

# init
app = Flask(__name__)
app.config['SECRET_KEY'] = 'e8b7e89b5a98e0c3e6f2d4a9b30c3a9d2f7a8b92e4a1c8d5f6e3b7d5c9f1e2a3'

# routes
bcrypt.init_app(app)
app.register_blueprint(index_bp, url_prefix='/')
app.register_blueprint(auth_bp, url_prefix='/auth')

if __name__ == "__main__":
    app.run(debug=True)
