import os
from flask import Flask, render_template_string
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_user import login_required, UserManager, UserMixin, SQLAlchemyAdapter

# Use a Class-based config to avoid needing a 2nd file
# os.getenv() enables configuration through OS environment variables
class ConfigClass(object):
    # Flask settings
    SECRET_KEY =              os.getenv('SECRET_KEY',       'THIS IS AN INSECURE SECRET')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL',     'sqlite:///basic_app.sqlite')
    CSRF_ENABLED = True

    # Flask-Mail settings
    MAIL_USERNAME =           os.getenv('MAIL_USERNAME',        'snpssite@gmail.com')
    MAIL_PASSWORD =           os.getenv('MAIL_PASSWORD',        'curispassword')
    MAIL_DEFAULT_SENDER =     os.getenv('MAIL_DEFAULT_SENDER',  '"SNPS Website" <noreply@example.com>')
    MAIL_SERVER =             os.getenv('MAIL_SERVER',          'smtp.gmail.com')
    MAIL_PORT =           int(os.getenv('MAIL_PORT',            '465'))
    MAIL_USE_SSL =        int(os.getenv('MAIL_USE_SSL',         True))

    # Flask-User settings
    USER_APP_NAME        = "SNPSsite"                # Used by email templates

def create_app():
    """ Flask application factory """
    
    # Initialize the Flask application
    app = Flask(__name__)
    app.secret_key = 'some_secret'
    
    # Setup Flask app and app.config
    app.config.from_object(__name__+'.ConfigClass')
    # Path to the upload directory
    APP_ROOT = os.path.dirname(os.path.abspath(__file__))
    UPLOAD_FOLDER = os.path.join(APP_ROOT, 'uploads')
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    # Acceptatble extensions for upload
    app.config['ALLOWED_EXTENSIONS'] = set(['txt'])
    
    # Initialize Flask extensions
    db = SQLAlchemy(app)                            # Initialize Flask-SQLAlchemy
    mail = Mail(app)                                # Initialize Flask-Mail
    
    # Define the User data model. Make sure to add flask.ext.user UserMixin !!!
    class User(db.Model, UserMixin):
        id = db.Column(db.Integer, primary_key=True)

        # User authentication information
        username = db.Column(db.String(50), nullable=False, unique=True)
        password = db.Column(db.String(255), nullable=False, server_default='')
        reset_password_token = db.Column(db.String(100), nullable=False, server_default='')

        # User email information
        email = db.Column(db.String(255), nullable=False, unique=True)
        confirmed_at = db.Column(db.DateTime())

        # User information
        active = db.Column('is_active', db.Boolean(), nullable=False, server_default='0')
        first_name = db.Column(db.String(100), nullable=False, server_default='')
        last_name = db.Column(db.String(100), nullable=False, server_default='')

        # User SNP file information
        #snp_file = db.Column(db.String(255))

    # Create all database tables
    db.create_all()

    # Setup Flask-User
    db_adapter = SQLAlchemyAdapter(db, User)        # Register the User model
    user_manager = UserManager(db_adapter, app)     # Initialize Flask-User

    return app
