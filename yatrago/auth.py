import re
from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from yatrago import db
from yatrago.models import User

auth = Blueprint("auth", __name__, url_prefix="/auth")
EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        error = None
        if not name or len(name) > 100:
            error = "Enter your name (up to 100 characters)."
        elif not EMAIL_PATTERN.fullmatch(email) or len(email) > 254:
            error = "Enter a valid email address."
        elif len(password) < 8:
            error = "Choose a password with at least 8 characters."
        elif password != confirm:
            error = "The passwords do not match."
        elif User.query.filter_by(email=email).first():
            error = "An account with that email already exists."
        if error:
            flash(error, "error")
            return render_template("auth/register.html")
        user = User(name=name, email=email)
        user.set_password(password)
        db.session.add(user)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            flash("An account with that email already exists.", "error")
            return render_template("auth/register.html")
        login_user(user)
        flash("Your YatraGo account is ready. Let’s plan a journey.", "success")
        return redirect(url_for("main.dashboard"))
    return render_template("auth/register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash("The email or password you entered is incorrect.", "error")
            return render_template("auth/login.html")
        login_user(user)
        next_url = request.args.get("next", "")
        parsed_next = urlsplit(next_url)
        if next_url.startswith("/") and not next_url.startswith("//") and not parsed_next.netloc:
            return redirect(next_url)
        return redirect(url_for("main.dashboard"))
    return render_template("auth/login.html")


@auth.post("/logout")
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("main.home"))
