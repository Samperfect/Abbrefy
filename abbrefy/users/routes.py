from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash, session
from datetime import datetime
from abbrefy.users.forms import RegistrationForm, LoginForm, ForgotPassword, ResetPassword
from abbrefy.users.models import User
from abbrefy.users.tools import login_required, no_login_required, validate_username, find_user
# attaching the users blueprint
users = Blueprint('users', __name__)


# the signup route
@users.route('/auth/signup/', methods=['GET', 'POST'])
@no_login_required
def signup():

    # instantiationg the form
    form = RegistrationForm()

    # defining the site title
    site_title = "Abbrefy | Power With Every Link"

    # handling form validation
    if form.validate_on_submit():

        new_user = User(form.username.data,
                        form.email.data, form.password.data)

        response = new_user.signup()

        # sending flased message
        if response == True:
            flash(
                "Welcome to Abbrefy", "success")
            return redirect(url_for('users.dashboard'))

        else:
            # sending flased message
            flash(
                "Sign Up Failed. Please Try Again", "danger")

    return render_template('signup.html', datetime=datetime, form=form, site_title=site_title)


# the signin route
@users.route('/auth/signin/', methods=['GET', 'POST'])
@no_login_required
def signin():

    # instantiationg the form
    form = LoginForm()
    # defining the site title
    site_title = "Abbrefy | Power With Every Link"

    # handling form validation
    if form.validate_on_submit():
        data = {
            "identifier": form.identifier.data,
            "password": form.password.data
        }
        user = User().signin(data)

        if user == False:
            flash('Invalid Signin Details', "danger")

        else:
            username = user['username']
            flash(f'Welcome back {username}', "success")
            return redirect(url_for('users.dashboard'))

    return render_template('signin.html', datetime=datetime, site_title=site_title, form=form)


# the forgot password route
@users.route('/auth/forgot/', methods=['POST', 'GET'])
@no_login_required
def forgot():
    # instantiationg the form
    form = ForgotPassword()
    # defining the site title
    site_title = "Abbrefy | Let's Get You Back In"

    # handling form validation
    if form.validate_on_submit():

        email = form.email.data

        User().reset_password(email)
        flash('Please Check Your Mail to Finish Your Password Reset', 'success')
        return redirect(url_for('users.signin'))

    return render_template('forgot.html', site_title=site_title, form=form, datetime=datetime)


# the forgot password route
@users.route('/auth/reset/', methods=['GET', 'POST'])
@no_login_required
def reset():
    # instantiationg the form
    form = ResetPassword()
    # defining the site title
    site_title = "Abbrefy | You're Almost In"
    # getting the finder query parameter
    finder = request.args.get('finder')
    # checking if the query parameter was passed
    if not finder:
        flash('Your reset link is invalid', 'danger')
        return redirect(url_for('users.forgot'))
    # checking if the query parameter matches any user
    user = find_user(finder)
    if not user:
        flash('Your reset link is invalid', 'danger')
        return redirect(url_for('users.forgot'))
    # handling form validation
    if form.validate_on_submit():
        password = form.password.data
        status = User().update_password(user, password)
        if status:
            return redirect(url_for('users.signin'))
        flash('Something went wrong', 'danger')
    return render_template('reset.html', site_title=site_title, form=form, datetime=datetime)


# the dashboard route
@users.route('/me/dashboard/')
@login_required
def dashboard(user):

    site_title = "Abbrefy | Grow As You Abbrefy"
    links = User.my_links(user['public_id'])
    keys = User.get_keys(user['public_id'])

    return render_template('dashboard.html', datetime=datetime, site_title=site_title, links=links, len=len, keys=keys)


# the signout route
@users.route('/auth/signout/', methods=['GET'])
@login_required
def signout(user):
    response = User.signout()
    if response:
        return redirect(url_for('main.home'))


# the update profile route
@users.route('/auth/profile/', methods=['POST'])
@login_required
def profile(user):
    try:

        # getting the request data
        data = request.get_json()
        # validating the data was sent
        if not data:
            return jsonify({"status": False, "error": "DATA_ERROR"}), 400
        # validating the username character context
        if not validate_username(data['usernameData']):
            return jsonify({"status": False,
                            "error": "DATA_VALIDATION_ERROR"}), 400
        # validating the username length
        if len(data['usernameData']) > 10 or len(data['usernameData']) < 3:
            return jsonify({"status": False,
                            "error": "CHARACTER_LIMIT_ERROR"}), 400

        # creating the URL object and abbrefying it
        if not "current_user" in session:
            return jsonify({"status": False, "error": "AUTHORIZATION_ERROR"}), 401

        user = session['current_user']['public_id']
        response = User().update_profile(user, data)

        if response == False:
            return jsonify({"status": False, "error": "PASSWORD_MATCH_ERROR"}), 400

        if response == True:
            return jsonify({"status": False, "error": "SECURE_PASSWORD_ERROR"}), 400

        if response['status'] == False:
            return jsonify({"status": False, "error": "UNKNOWN_ERROR"}), 400

        return jsonify({"status": True, "message": "UPDATE_SUCCESS", "data": response}), 200

    # handling errors
    except KeyError:
        return jsonify({"status": False, "error": "DATA_ERROR"}), 400

    except:
        return jsonify({"status": False, "error": "UNKNOWN_ERROR"}), 400


# the API Key route
@users.route('/auth/account/apiKey/', methods=['POST'])
@login_required
def create(user):
    try:

        # getting the request data
        data = request.get_json()
        # validating the data was sent
        if not data:
            return jsonify({"status": False, "error": "DATA_ERROR"}), 400

        # creating the URL object and abbrefying it
        if not "current_user" in session:
            return jsonify({"status": False, "error": "AUTHORIZATION_ERROR"}), 401

        user = user['public_id']
        response = User().generate_api_key(user)

        if response == False:
            return jsonify({"status": False, "error": "KEY_LIMIT_EXCEEDED"}), 400

        if response['status'] == False:
            return jsonify({"status": False, "error": "UNKNOWN_ERROR"}), 400

        return jsonify({"status": True, "message": "CREATE_SUCCESS", "data": response}), 200

    # handling errors
    except KeyError:
        return jsonify({"status": False, "error": "DATA_ERROR"}), 400

    except:
        return jsonify({"status": False, "error": "UNKNOWN_ERROR"}), 400


# the API Key route
@users.route('/auth/account/apiKey/delete', methods=['DELETE'])
@login_required
def delete(user):
    try:

        # getting the request data
        data = request.get_json()
        # validating the data was sent
        if not data:
            return jsonify({"status": False, "error": "DATA_ERROR"}), 400

        # creating the URL object and abbrefying it
        if not "current_user" in session:
            return jsonify({"status": False, "error": "AUTHORIZATION_ERROR"}), 401

        response = User().delete_api_key(user['public_id'], data['apiKey'])

        if response == False:
            return jsonify({"status": False, "error": "AUTHORIZATION_ERROR"}), 401

        if response['status'] == False:
            return jsonify({"status": False, "error": "UNKNOWN_ERROR"}), 400

        return jsonify({"status": True, "message": "DELETE_SUCCESS", "data": response}), 200

    # handling errors
    except KeyError:
        return jsonify({"status": False, "error": "DATA_ERROR"}), 400

    except:
        return jsonify({"status": False, "error": "UNKNOWN_ERROR"}), 400
