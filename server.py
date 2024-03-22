from datetime import datetime
from flask import Flask, flash, jsonify, render_template, request, url_for, redirect
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from flask_bcrypt import Bcrypt
from talisman import Talisman
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError
import json
import untis
import config_manager

config = config_manager.Config("settings.json")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = config.get_config("database_uri")
app.config['SECRET_KEY'] = config.get_config("encryption_secret_key")

talisman = Talisman(app, force_https=True)

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    semesters = db.Column(db.TEXT)
    modules = db.Column(db.TEXT)
    start_date = db.Column(db.TEXT)
    end_date = db.Column(db.TEXT)

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=3, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Register')

    def validate_username(self, username):
        existing_user_username = User.query.filter_by(username=username.data).first()
        if existing_user_username:
            raise ValidationError('That username already exists. Please choose a different one.')

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=3, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                flash('Incorrect password. Please try again.', 'error')
        else:
            flash('User does not exist. Please register.', 'error')
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    existing_user_username = User.query.filter_by(username=form.username.data).first()
    if existing_user_username:
        flash('That username already exists. Please choose a different one.', 'error')
    else:
        if form.validate_on_submit():
            hashed_password = bcrypt.generate_password_hash(form.password.data)
            new_user = User(username=form.username.data, password=hashed_password, semesters=json.dumps({}), modules=json.dumps({}), start_date=config.get_config("minimum_start_date"), end_date=config.get_config("maximum_end_date"))
            db.session.add(new_user)
            db.session.commit()
            flash('Registration successful. You can now log in.', 'success')
            return redirect(url_for('login'))
            
    return render_template('register.html', form=form)

@app.route('/get_semester_list')
def get_semester_list():
    return jsonify(untis.get_all_semesters())

@app.route('/process_semester_selection', methods=['POST'])
@login_required
def process_semester_selection():
    selected_items = request.form.getlist('selected_items')

    if current_user.is_authenticated:
        current_user.semesters = json.dumps(selected_items)
        db.session.commit()
    else:
        print("User is not authenticated")

    return ""

@app.route('/get_module_list')
def get_module_list():
    semesters = json.loads(current_user.semesters)
    start_date = datetime.strptime(current_user.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(current_user.end_date, '%Y-%m-%d')
    all_modules = untis.get_all_modules_of_semesters(semesters=semesters, start_date=start_date, end_date=end_date)
    return jsonify(all_modules)

@app.route('/process_module_selection', methods=['POST'])
@login_required
def process_module_selection():
    selected_items = request.form.getlist('selected_items')

    if current_user.is_authenticated:
        current_user.modules = json.dumps(selected_items)
        db.session.commit()
    else:
        print("User is not authenticated")

    return ""

@app.route('/set_date', methods=['POST'])
@login_required
def set_date():
    start_date_str = request.form.get('startDateInput')
    end_date_str = request.form.get('endDateInput')
    min_start_date_str = config.get_config("minimum_start_date")
    max_end_date_str = config.get_config("maximum_end_date")

    if datetime.strptime(start_date_str, "%Y-%m-%d") < datetime.strptime(min_start_date_str, "%Y-%m-%d"):
        start_date_str = min_start_date_str
    if datetime.strptime(end_date_str, "%Y-%m-%d") > datetime.strptime(max_end_date_str, "%Y-%m-%d"):
        end_date_str = max_end_date_str

    current_user.start_date = start_date_str
    current_user.end_date = end_date_str
    db.session.commit()
    return jsonify({'start_date': start_date_str, 'end_date': end_date_str})

@app.route('/get_date', methods=['GET'])
def get_date():
    return jsonify({'start_date': current_user.start_date, 'end_date': current_user.end_date})

@app.route('/reset_date', methods=['POST'])
@login_required
def reset_date():
    min_start_date_str = config.get_config("minimum_start_date")
    max_end_date_str = config.get_config("maximum_end_date")

    current_user.start_date = min_start_date_str
    current_user.end_date = max_end_date_str
    db.session.commit()
    return jsonify({'start_date': min_start_date_str, 'end_date': max_end_date_str})

## ----- MAIN ----- ##

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=443, ssl_context=('ssl/certificate.crt', 'ssl/privatekey.key'))
