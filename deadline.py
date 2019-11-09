from flask import Flask, render_template
from flask_admin import Admin
from flask_basicauth import BasicAuth
from flask_admin.contrib.sqla import ModelView
import os
from flask import Flask, url_for, redirect, render_template, request
from flask_sqlalchemy import SQLAlchemy
from wtforms import form, fields, validators,widgets
import flask_admin as admin
import flask_login as login
from flask_admin.contrib import sqla
from flask_admin import helpers, expose
from werkzeug.security import generate_password_hash, check_password_hash
import os.path as op




app = Flask(__name__)
import random
key = random.randint(0,10000)


# Create dummy secrey key so we can use sessions
app.config['SECRET_KEY'] = str(key)

# Create in-memory database
app.config['DATABASE_FILE'] = 'sample_db.sqlite'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + app.config['DATABASE_FILE']
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

class Page(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(64))
    text = db.Column(db.UnicodeText)

    def __unicode__(self):
        return self.name

class Aboutme(db.Model):
    __tablename__ = "aboutme"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.UnicodeText)

    def __unicode__(self):
        return self.name

# Create user model.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(64))




    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return self.id

    def __unicode__(self):
        return self.username


# Define login and registration forms (for flask-login)
class LoginForm(form.Form):
    login = fields.StringField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        # we're comparing the plaintext pw with the the hash from the db
        if not check_password_hash(user.password, self.password.data):
        # to compare plain text passwords use
        # if user.password != self.password.data:
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return db.session.query(User).filter_by(login=self.login.data).first()


class RegistrationForm(form.Form):
    login = fields.StringField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        if db.session.query(User).filter_by(login=self.login.data).count() > 0:
            raise validators.ValidationError('Duplicate username')


# Initialize flask-login
def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.query(User).get(user_id)

class CKTextAreaWidget(widgets.TextArea):
    def __call__(self, field, **kwargs):
        # add WYSIWYG class to existing classes
        existing_classes = kwargs.pop('class', '') or kwargs.pop('class_', '')
        kwargs['class'] = '{} {}'.format(existing_classes, "ckeditor")
        return super(CKTextAreaWidget, self).__call__(field, **kwargs)

class CKTextAreaField(fields.TextAreaField):
    widget = CKTextAreaWidget()



# Create customized model view class
class MyModelView(sqla.ModelView):

    def is_accessible(self):
        return login.current_user.is_authenticated

class PageView(sqla.ModelView):
    form_overrides = {
        'text': CKTextAreaField
    }
    create_template = 'create_page.html'
    edit_template = 'edit_page.html'


class MyAdminIndexView(admin.AdminIndexView):

    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login
        form = LoginForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = form.get_user()
            login.login_user(user)

        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        self._template_args['form'] = form
        return super(MyAdminIndexView, self).index()


    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))


#index page
@app.route("/", methods=['GET', 'POST'])
def index():
    post = Page.query.all()
    return render_template("index.html",post=post)

#/aboutme
@app.route("/about_me" ,methods = ['POST','GET'])
def aboutme():
    aboutme = Aboutme.query.all()
    return render_template("aboutme.html",aboutme=aboutme)

#error page
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'),404

#error page
@app.errorhandler(500)
def internal_server_error(e):
    return render_template('internal_error.html'),500

# Initialize flask-login
init_login()

# Create admin
admin = admin.Admin(app, 'Deadline AdminPanel', index_view=MyAdminIndexView(), base_template='admin.html')

# Add view
admin.add_view(MyModelView(User,db.session))
admin.add_view(MyModelView(Page,db.session))
admin.add_view(MyModelView(Aboutme,db.session))


def build_sample_db():
    import string
    import random

    db.drop_all()
    db.create_all()
    # passwords are hashed, to use plaintext passwords instead:
    #test_user = User(login="admin", password="admin")
    first_post = Page(name="My_first_post",text="my first post :)")
    test_user = User(login="admin", password=generate_password_hash("admin"))
    first_aboutme = Aboutme(text = """Hi my name is Kostas im a university student and I build this website to share my experience,
    thoughts and ideas in programming with you...propably you will only see python as I am bored to learn another programming language...""")
    db.session.add(test_user)
    db.session.add(first_post)
    db.session.add(first_aboutme)
    db.session.commit()
    return

if __name__ == '__main__':
    app_dir = os.path.realpath(os.path.dirname(__file__))
    database_path = os.path.join(app_dir, app.config['DATABASE_FILE'])
    if not os.path.exists(database_path):
        build_sample_db()

if __name__ == '__main__':
    app.run(debug="True")
