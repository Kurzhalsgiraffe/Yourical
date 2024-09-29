import ical_manager
import json
from datetime import datetime
from flask import Flask, flash, jsonify, render_template, request, send_from_directory, url_for, redirect
from flask_apscheduler import APScheduler
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, EqualTo

manager = ical_manager.IcalManager(config_file="config/settings.json")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = manager.config.get_config("database_uri")
app.config['SECRET_KEY'] = manager.config.get_config("encryption_secret_key")
CORS(app)

scheduler = APScheduler()
scheduler.api_enabled = True
scheduler.init_app(app)
scheduler.start()

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
    additional_calendars = db.Column(db.TEXT)
    register_date = db.Column(db.TEXT)
    last_login = db.Column(db.TEXT)
    last_calendar_pull = db.Column(db.TEXT)

class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=3, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8)], render_kw={"placeholder": "Password"})
    confirm_password = PasswordField(validators=[InputRequired(), EqualTo('password', message='Passwords must match')], render_kw={"placeholder": "Confirm Password"})
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=3, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=8, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField('Login')

# ------ Page Routes  ------

@app.route('/')
def index():
    domain = request.scheme + '://' + request.host
    return render_template('index.html', current_user=current_user, domain=domain)

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    domain = request.scheme + '://' + request.host
    return render_template('dashboard.html', current_user=current_user, domain=domain)

@app.route('/faq', methods=['GET'])
def faq():
    domain = request.scheme + '://' + request.host
    return render_template('faq/faq.html', domain=domain)

@app.route('/faq/google', methods=['GET'])
def faq_google():
    return render_template('faq/faq_google.html')

@app.route('/faq/apple', methods=['GET'])
def faq_apple():
    return render_template('faq/faq_apple.html')

@app.route('/faq/outlook', methods=['GET'])
def faq_outlook():
    return render_template('faq/faq_outlook.html')

@app.route('/privacy_policy', methods=['GET'])
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.username.data:
        username = form.username.data.lower()
        if form.validate_on_submit():
            user = User.query.filter_by(username=username).first()
            if user:
                if bcrypt.check_password_hash(user.password, form.password.data):
                    login_user(user)
                    manager.log_login(user.username)
                    current_user.last_login = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    db.session.commit()
                    return redirect(url_for('dashboard'))
                else:
                    flash('- Incorrect password. Please try again.', 'error')
            else:
                flash('- User does not exist. Please register.', 'error')
    return render_template('login.html', form=form)

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@ app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.username.data:
        username = form.username.data.lower()
        existing_user_username = User.query.filter_by(username=username).first()
        if existing_user_username or not username.isalnum() or username in manager.config.get_config("banned_usernames") or form.password.data != form.confirm_password.data:
            if not username.isalnum():
                flash('- Only alphanumerical Characters are allowed. Please choose a different name.', 'error')
            if existing_user_username:
                flash('- That username already exists. Please choose a different name.', 'error')
            if username in manager.config.get_config("banned_usernames"):
                flash('- That username is not allowed. Please choose a different name.', 'error')
            if form.password.data != form.confirm_password.data:
                flash('- Passwords do not match.', 'error')
        else:
            if form.validate_on_submit():
                hashed_password = bcrypt.generate_password_hash(form.password.data)
                new_user = User(username=username, password=hashed_password, semesters="", modules="", additional_calendars="", register_date="", last_login="", last_calendar_pull="")
                new_user.register_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                db.session.add(new_user)
                db.session.commit()
                flash('- Registration successful. You can now log in.', 'success')
                return redirect(url_for('login'))

    return render_template('register.html', form=form)

# ------ Functional Routes  ------

@app.route('/get_semester_list')
def get_semester_list():
    selected_semesters = json.loads(current_user.semesters) if current_user.semesters else None
    selected_additionals = json.loads(current_user.additional_calendars) if current_user.additional_calendars else None
    semester_list = manager.get_semester_list(selected_semesters=selected_semesters, selected_additionals=selected_additionals)
    return jsonify(semester_list)

@app.route('/process_semester_selection', methods=['POST'])
@login_required
def process_semester_selection():
    selected_items = request.form.getlist('selected_items')
    additional_calendars = [value for value in selected_items if value in manager.netloader.data.get("names")]

    additional = [item for item in selected_items if item in additional_calendars]
    semesters = [item for item in selected_items if item not in additional_calendars]

    if current_user.is_authenticated:
        current_user.semesters = json.dumps(semesters)
        current_user.additional_calendars = json.dumps(additional)
        db.session.commit()
        return jsonify({"message": "Selection saved"}), 200
    else:
        print("User is not authenticated")
        return jsonify({"message": "User is not authenticated"}), 401

@app.route('/get_module_list')
def get_module_list():
    all_modules = []
    if current_user.semesters:
        semesters = json.loads(current_user.semesters)
        all_modules = manager.untis_handler.get_module_list_of_semesters(semesters=semesters)

        if current_user.modules:
            selection = json.loads(current_user.modules)
            for i in all_modules:
                i["selected"] = i["name"] in selection
    return jsonify(all_modules)

@app.route('/process_module_selection', methods=['POST'])
@login_required
def process_module_selection():
    selected_items = request.form.getlist('selected_items')

    if current_user.is_authenticated:
        current_user.modules = json.dumps(selected_items)
        db.session.commit()
        manager.generate_single_ical(current_user.username)
        return jsonify({"message": "Selection saved"}), 200
    else:
        print("User is not authenticated")
        return jsonify({"message": "User is not authenticated"}), 401

# ------ Download Routes  ------

@app.route('/ical/<username>')
def serve_file(username):
    directory = 'calendars'
    try:
        user = User.query.filter_by(username=username).first()
        user.last_calendar_pull = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        db.session.commit()

        ip_address = request.headers.get('X-Forwarded-For', request.remote_addr)
        manager.log_ical_request(ip_address, username)

        return send_from_directory(directory, f"{username}.calendar.ics")
    except FileNotFoundError:
        return "file not found", 404

# -- custom routes for .ics files of not generated by this application. Those .ics files must be deployed manually in dir calendars/

@app.route('/sia')
def serve_sia():
    directory = 'calendars'
    try:
        return send_from_directory(directory, "sia.calendar.ics")
    except FileNotFoundError:
        return "file not found", 404

@app.route('/vdi')
def serve_vdi():
    directory = 'calendars'
    try:
        return send_from_directory(directory, "vdi.calendar.ics")
    except FileNotFoundError:
        return "file not found", 404

# ------ Scheduler  ------

@scheduler.task('interval', id='update_calendars', seconds=manager.config.get_config("seconds_between_calendar_updates"), misfire_grace_time=900)
def update_calendars():
    manager.untis_handler.update_schoolyear_from_untis()
    manager.untis_handler.update_all_tables_from_untis()
    manager.netloader.download_additional_calendars()
    manager.netloader.icals_to_event_list()
    manager.generate_all_icals()

## ----- MAIN ----- ##

if __name__ == "__main__":
    app.run(host="127.0.0.1", debug=True)
