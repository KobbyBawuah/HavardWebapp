import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")


@app.route("/")
@login_required
def index():
    """Show account balance"""
    rows = db.execute("SELECT cash FROM users WHERE  id =:user_id", user_id=session["user_id"])
    current_cash = rows[0]["cash"]

    return render_template("index.html", current_cash = usd(current_cash))



@app.route("/transactions")
@login_required
def transactions():
    """Show options for transactions"""
    return render_template("transactions.html")


def isFilled(field):
    if not request.form.get(field):
         return apology(f"must provide {field}", 403)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username and password was submitted
        result_checks = isFilled("username") or isFilled("password")
        if result_checks is not None:
            return result_checks

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        result_checks = isFilled("username") or isFilled("password") or isFilled("confirmation")
        if result_checks is not None:
            return result_checks
        if request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords don't match")
        #reference from Deliberate Think
        try:
            primary = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username = request.form.get("username"), hash=generate_password_hash(request.form.get("password")))
        except:
            return apology("User name is already in use", 403)
        if primary is None:
            return apology("registration error", 403)

        session["user_id"] = primary
        return redirect("/")


@app.route("/find_food", methods=["GET"])
@login_required
def find_food():
        return render_template("find_food.html")

@app.route("/map", methods=["GET"])
@login_required
def map():
        return render_template("map.html")

@app.route("/add_money", methods=["GET", "POST"])
@login_required
def add_money():
    if request.method == "POST":
        db.execute("UPDATE users SET cash=cash+:amount WHERE id=:user_id", amount = request.form.get("money"), user_id=session["user_id"])
        return (redirect("/"))
    else:
        return render_template("add_money.html")

@app.route("/remove_money", methods=["GET", "POST"])
@login_required
def remove_money():
    if request.method == "POST":
        db.execute("UPDATE users SET cash=cash-:amount WHERE id=:user_id", amount = request.form.get("money"), user_id=session["user_id"])
        return (redirect("/"))
    else:
        return render_template("remove_money.html")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
