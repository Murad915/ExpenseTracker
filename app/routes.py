import json
from collections import defaultdict
from datetime import date

import plotly.graph_objects as go
import plotly.utils
from flask import abort, Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from . import db
from .ai_engine import CATEGORIES, categorize_expense
from .models import Expense

main_bp = Blueprint("main", __name__)

_CHART_COLORS = [
    "#6366f1", "#22d3ee", "#10b981", "#f59e0b", "#ec4899",
    "#8b5cf6", "#f97316", "#14b8a6", "#a78bfa", "#34d399",
    "#60a5fa", "#fb7185",
]


@main_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        amount = request.form.get("amount", "").strip()
        description = request.form.get("description", "").strip()

        if not amount or not description:
            flash("Amount and description are required.", "error")
            return redirect(url_for("main.index"))

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Amount must be a positive number.", "error")
            return redirect(url_for("main.index"))

        manual_category = request.form.get("category", "").strip()
        category = manual_category or categorize_expense(description, amount)

        db.session.add(
            Expense(
                user_id=current_user.id,
                amount=amount,
                category=category,
                description=description,
                date=date.today(),
            )
        )
        db.session.commit()
        return redirect(url_for("main.index"))

    expenses = (
        Expense.query
        .filter_by(user_id=current_user.id)
        .order_by(Expense.date.desc(), Expense.id.desc())
        .all()
    )
    return render_template("index.html", expenses=expenses, categories=CATEGORIES)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    expenses = Expense.query.filter_by(user_id=current_user.id).all()

    if not expenses:
        return render_template("dashboard.html", chart_json=None, stats=None)

    totals = defaultdict(float)
    for e in expenses:
        totals[e.category] += float(e.amount)

    total_spent = sum(totals.values())
    top_category = max(totals, key=totals.get)
    colors = [_CHART_COLORS[i % len(_CHART_COLORS)] for i in range(len(totals))]

    fig = go.Figure(
        go.Pie(
            labels=list(totals.keys()),
            values=list(totals.values()),
            hole=0.55,
            marker=dict(colors=colors, line=dict(color="#030712", width=2)),
            textinfo="label+percent",
            textfont=dict(size=12, color="#e5e7eb"),
            hovertemplate="<b>%{label}</b><br>$%{value:.2f}<br>%{percent}<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e5e7eb", family="ui-sans-serif, system-ui, sans-serif"),
        legend=dict(
            font=dict(color="#9ca3af", size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(t=20, b=20, l=20, r=20),
        showlegend=True,
    )

    stats = {
        "total_spent": total_spent,
        "expense_count": len(expenses),
        "category_count": len(totals),
        "top_category": top_category,
    }
    chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template("dashboard.html", chart_json=chart_json, stats=stats)


@main_bp.route("/edit/<int:expense_id>", methods=["GET", "POST"])
@login_required
def edit(expense_id):
    expense = db.get_or_404(Expense, expense_id)

    if expense.user_id != current_user.id:
        abort(403)

    if request.method == "POST":
        amount = request.form.get("amount", "").strip()
        description = request.form.get("description", "").strip()

        if not amount or not description:
            flash("Amount and description are required.", "error")
            return redirect(url_for("main.edit", expense_id=expense_id))

        try:
            amount = float(amount)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Amount must be a positive number.", "error")
            return redirect(url_for("main.edit", expense_id=expense_id))

        expense.amount = amount
        expense.description = description
        db.session.commit()
        flash("Expense updated.", "success")
        return redirect(url_for("main.index"))

    return render_template("edit.html", expense=expense)


@main_bp.route("/delete/<int:expense_id>", methods=["POST"])
@login_required
def delete(expense_id):
    expense = db.get_or_404(Expense, expense_id)

    if expense.user_id != current_user.id:
        abort(403)

    db.session.delete(expense)
    db.session.commit()
    return redirect(url_for("main.index"))
