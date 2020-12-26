import os

from datetime import datetime
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

#Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""
    table = session["user_id"]
    table = str(table)
    db.execute("CREATE TABLE IF NOT EXISTS :table('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'symbol' TEXT NOT NULL, 'name' TEXT NOT NULL, 'shares' INTEGER NOT NULL, 'price' NUMERIC NOT NULL, 'TOTAL' NUMERIC NOT NULL);", table=table)
    cash = db.execute("SELECT cash from users where id = :id;", id=session["user_id"])
    data = db.execute("SELECT * FROM :table", table=table)
    for i in cash:
        formatted_float = usd(i['cash'])
        return render_template("index.html", cash=formatted_float, data=data, id=session["user_id"], usd=usd)

    # return render_template("index.html", data=data)

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # If the request method is get mean get the page then we'll show the form
    if request.method == "GET":
        return render_template("buy.html")
    # else if not the via request method is Get mean the form is submited then check ....
    else:
        symbol = lookup(request.form.get("symbol").lower())
        if not request.form.get("symbol"):
            return apology("Missing symbol", 400)
        if not request.form.get("share"):
            return apology("Missing share", 400)
        if symbol == None:
            return apology("Invalid Symbol", 400)
        cash = db.execute("select cash from users where id = :id;", id=session["user_id"])
        price = "price"
        final_value = 0
        for i in range(int(request.form.get("share"))):
            final_value = final_value + symbol[price]

        for i in cash:
            if i['cash'] < final_value:
                return apology("Can't Afford", 400)


        table = session["user_id"]
        table = str(table)

        db.execute("INSERT INTO :table(symbol, name, shares, price, TOTAL) VALUES(:symbol, :name, :shares, :price, :total);", symbol=symbol['symbol'], name=symbol['name'], shares=request.form.get("share"), price=usd(symbol['price']), total=usd(final_value), table=table)
        db.execute("UPDATE users SET cash = :cash where id = :id;", id = session["user_id"], cash = i['cash'] - final_value)
        now = datetime.now()
        dt_string = dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
        db.execute("INSERT INTO history(symbol, shares, price, Transacted) VALUES(:symbol, :shares, :price, :transacted)", symbol=request.form.get("symbol"), shares=request.form.get("share"), price=usd(symbol['price']), transacted=dt_string)
        return redirect("/")


            # name = "symbol"
            # a = "name"
            # db.execute("create table IF NOT EXISTS stocks ('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'symbol' TEXT NOT NULL, 'name' TEXT NOT NULL, 'shares' INTEGER NOT NULL, 'price' NUMERIC NOT NULL, 'TOTAL' NUMERIC NOT NULL);")
            # # db.execute("INSERT INTO :table (symbol, name, shares, price, TOTAL) VALUES (:symbol, :name, :shares, :price, :TOTAL)", symbol=symbol[name], name=symbol[a], shares=request.form.get("share"), price=symbol[price], table=symbol[name], TOTAL=final_value)
            # # db.execute("UPDATE users SET cash = :cash where id = :id;", id = session["user_id"], cash = i['cash'] - final_value)
            # # for i in symbol:
            # if "symbols" not in session:
            #     session["symbols"] = symbol['symbol']
            # if "names" not in session:
            #     session["names"] = symbol['name']
            # if "shares" not in session:
            #     session["shares"] = request.form.get("share")
            # if "price" not in session:
            #     session["price"] = symbol['price']

            # db.execute("INSERT INTO stocks (id, symbol, name, shares, price, TOTAL) VALUES( :id, :symbol, :name, :shares, :price, :TOTAL);", id=session["user_id"], symbol=session["symbols"], name=session["names"], shares=session["shares"], price=session["price"], TOTAL=final_value)
            # db.execute("UPDATE users SET cash = :cash where id = :id;", id = session["user_id"], cash = i['cash'] - final_value)
            # return redirect("/")
            #return f"{symbol['name']}"

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    now = datetime.now()

    dt_string = now.strftime("%d-%m-%Y %H:%M:%S")

    table = session["user_id"]
    table = str(table)
    db.execute("CREATE TABLE IF NOT EXISTS :table('id' INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL, 'symbol' TEXT NOT NULL, 'name' TEXT NOT NULL, 'shares' INTEGER NOT NULL, 'price' NUMERIC NOT NULL, 'TOTAL' NUMERIC NOT NULL);", table=table)
    cash = db.execute("SELECT cash from users where id = :id;", id=session["user_id"])
    data = db.execute("SELECT * FROM history")
    for i in cash:
        formatted_float = usd(i['cash'])
        return render_template("history.html", cash=formatted_float, data=data, id=session["user_id"])


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    variable = True
    if request.method == "POST":
        look = lookup(request.form.get("quote").lower())
        if len(str(request.form.get("quote"))) == 0:
            return apology("Missing Symbol", 400)
        if look == None:
            return apology("Invalid Symbol", 400)
        else:
            return render_template("quote.html", variable=variable, look=look)
    elif request.method == "GET":
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        cash = 10000.00
        rows = db.execute("SELECT * FROM users;")
        name = request.form.get("register_username")
        password = request.form.get("register_password")
        password_again = request.form.get("register_password_again")

        password = generate_password_hash(str(password))
        password_again = generate_password_hash(str(password_again))
        if check_password_hash(password, password_again):
            return apology("INCORRECT USERNAME OR PASSWORD", 403)
        for row in rows:
            if str(name) in row["username"]:
                return apology("The username is Exists Choose another username", 403)

        db.execute("INSERT INTO users(username, hash, cash) VALUES(?, ?, ?)", name, password, cash)
        # session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("register.html")
    # return apology("TODO")

@app.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "GET":
        return render_template("change_password.html")
    else:
        if not request.form.get("cash"):
            return apology("Missing Cash Field", 400)
        # if int(request.form.get("cash")) < 0:
        #     return apology("Could not add cash", 400)
        cash = db.execute("select cash from users where id = :id", id=session["user_id"])
        for i in cash:
            db.execute("UPDATE users SET cash = :cash where id = :id;", id=session["user_id"], cash=(int(i['cash']) + int(request.form.get('cash'))))
        #print("Hello")
            return redirect("/")


# @app.route("/add", methods=["GET", "POST"])
# def add():
#     if request.method == "GET":
#         return render_template("change_password.html")
#     else:
#         if not request.form.get("cash"):
#             return apology("Missing Cash Field", 400)
#         if int(request.form.get("cash")) < 0:
#             return apology("Could not add cash", 400)
#         cash = db.execute("select cash from users where id = :id", id=session["user"])

#         for i in cash:
#             db.execute("UPDATE users SET cash = :cash where id = :id", id=session["user_id"], cash=int(i['cash']) + int(request.form.get("cash"))
#             return redirect("/")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    now = datetime.now()

    dt_string = now.strftime("%Y-%m-%d %H:%M:%S")
    """Sell shares of stock"""
    if request.method == "GET":
        data = db.execute("select * from :table", table=str(session["user_id"]))
        return render_template("sell.html", data=data)
    # else if not the via request method is Get mean the form is submited then check ....
    else:
        #return f"{str(request.form.get('symbol'))}"
        if not request.form.get("symbol"):
            return apology("Missing Symbol", 403)
        if not request.form.get("shares"):
            return apology("Missing shares", 403)
        table = session["user_id"]
        table = str(table)

        share = db.execute("select shares from :table where symbol=:symbol", table=str(session["user_id"]), symbol=request.form.get("symbol"))
        for i in share:
            if int(request.form.get("shares")) > int(i['shares']):
                return apology("Too Much", 400)

        # if request.form.get("shares") >
        symbol = lookup(request.form.get("symbol"))
        cash = db.execute("select cash from users where id = :id;", id=session["user_id"])
        # price = "price"
        final_value = 0
        # return f"{symbol['price']}"
        for i in range(int(request.form.get("shares"))):
            final_value = final_value + symbol['price']

        # return f"{final_value}"
        # for i in cash:
        #     if i['cash'] < final_value:
        #         return apology("Can't Afford", 400)

        j = 0
        for i in share:
            j = j + symbol['price']
        for i in share:
            h = j + symbol['price']
            db.execute("UPDATE :table SET shares = :shares where symbol=:symbol;", symbol=request.form.get("symbol"), shares=int(i['shares']) - int(request.form.get("shares")), table=str(session["user_id"]))
            db.execute("UPDATE :table SET price = :price where symbol=:symbol", table=str(session["user_id"]), price=symbol['price'], symbol=request.form.get("symbol"))
            break
        for i in cash:
            db.execute("UPDATE :table SET TOTAL = :total where symbol=:symbol;", table=str(session["user_id"]), total=j, symbol=request.form.get("symbol"))
            db.execute("UPDATE users SET cash = :cash where id = :id;", id = session["user_id"], cash = i['cash'] + final_value)
            db.execute("INSERT INTO history(symbol, shares, price, Transacted) VALUES(:symbol, :shares, :price, :transacted)", symbol=request.form.get("symbol"), shares=f"-{request.form.get('shares')}", price=usd(symbol['price']), transacted=dt_string)
            return redirect("/")



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
