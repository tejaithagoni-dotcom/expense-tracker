from flask import Flask, render_template, request, redirect, Response
from flask_sqlalchemy import SQLAlchemy
from collections import defaultdict
import csv
import io


app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///expenses.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)



class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)



class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20), nullable=False)



@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        expense = Expense(
            amount=float(request.form["amount"]),
            category=request.form["category"],
            date=request.form["date"]
        )

        db.session.add(expense)
        db.session.commit()

        return redirect("/")



    selected_month = request.args.get("month")


    if selected_month:

        expenses = Expense.query.filter(
            Expense.date.like(f"{selected_month}%")
        ).all()

    else:

        expenses = Expense.query.all()



    total = sum(e.amount for e in expenses)



    category_totals = defaultdict(float)

    for expense in expenses:
        category_totals[expense.category] += expense.amount


    categories = dict(category_totals)



    expense_count = len(expenses)



    if categories:
        biggest_category = max(categories, key=categories.get)
    else:
        biggest_category = "None"



    budget = Budget.query.first()

    if budget:
        budget_amount = budget.amount
    else:
        budget_amount = 0


    remaining = budget_amount - total



    return render_template(
        "index.html",
        expenses=expenses,
        total=total,
        categories=categories,
        expense_count=expense_count,
        biggest_category=biggest_category,
        budget_amount=budget_amount,
        remaining=remaining
    )




@app.route("/delete/<int:id>")
def delete(id):

    expense = Expense.query.get(id)

    if expense:
        db.session.delete(expense)
        db.session.commit()

    return redirect("/")




@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):

    expense = Expense.query.get(id)


    if request.method == "POST":

        expense.amount = float(request.form["amount"])
        expense.category = request.form["category"]
        expense.date = request.form["date"]

        db.session.commit()

        return redirect("/")


    return render_template(
        "edit.html",
        expense=expense
    )




@app.route("/export")
def export():

    expenses = Expense.query.all()

    output = io.StringIO()

    writer = csv.writer(output)

    writer.writerow(["Amount", "Category", "Date"])


    for expense in expenses:

        writer.writerow([
            expense.amount,
            expense.category,
            expense.date
        ])


    response = Response(
        output.getvalue(),
        mimetype="text/csv"
    )


    response.headers["Content-Disposition"] = "attachment; filename=expenses.csv"


    return response




@app.route("/budget", methods=["POST"])
def budget():

    amount = float(request.form["budget"])


    old_budget = Budget.query.first()


    if old_budget:

        old_budget.amount = amount

    else:

        new_budget = Budget(amount=amount)
        db.session.add(new_budget)


    db.session.commit()


    return redirect("/")




if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)