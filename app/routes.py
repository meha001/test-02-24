from flask import Blueprint, flash, jsonify, redirect, render_template, request, url_for

from app import db
from app.models import Giveaway, Participant, Prize, Winner
from app.services import ensure_public_token, register_participant, run_draw

bp = Blueprint("main", __name__)

STATUS_LABELS = {
    "draft": "Черновик",
    "active": "Активен",
    "completed": "Завершён",
}


@bp.context_processor
def inject_globals():
    return {"STATUS_LABELS": STATUS_LABELS}


@bp.route("/")
def index():
    giveaways = Giveaway.query.order_by(Giveaway.created_at.desc()).all()
    stats = {
        "total": len(giveaways),
        "active": sum(1 for g in giveaways if g.status == "active"),
        "completed": sum(1 for g in giveaways if g.status == "completed"),
    }
    return render_template("index.html", giveaways=giveaways, stats=stats)


@bp.route("/giveaway/new", methods=["GET", "POST"])
def create_giveaway():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        if not title:
            flash("Укажите название розыгрыша", "error")
            return render_template("giveaway_form.html", giveaway=None)

        giveaway = Giveaway(title=title, description=description)
        ensure_public_token(giveaway)
        db.session.add(giveaway)
        db.session.commit()
        flash("Розыгрыш создан", "success")
        return redirect(url_for("main.giveaway_detail", id=giveaway.id))

    return render_template("giveaway_form.html", giveaway=None)


@bp.route("/giveaway/<int:id>")
def giveaway_detail(id):
    giveaway = Giveaway.query.get_or_404(id)
    ensure_public_token(giveaway)
    db.session.commit()
    public_url = url_for("main.public_register", token=giveaway.public_token, _external=True)
    return render_template("giveaway_detail.html", giveaway=giveaway, public_url=public_url)


@bp.route("/giveaway/<int:id>/edit", methods=["GET", "POST"])
def edit_giveaway(id):
    giveaway = Giveaway.query.get_or_404(id)
    if giveaway.status == "completed":
        flash("Завершённый розыгрыш нельзя редактировать", "error")
        return redirect(url_for("main.giveaway_detail", id=id))

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        if not title:
            flash("Укажите название", "error")
            return render_template("giveaway_form.html", giveaway=giveaway)

        giveaway.title = title
        giveaway.description = description
        db.session.commit()
        flash("Изменения сохранены", "success")
        return redirect(url_for("main.giveaway_detail", id=id))

    return render_template("giveaway_form.html", giveaway=giveaway)


@bp.route("/giveaway/<int:id>/status", methods=["POST"])
def update_status(id):
    giveaway = Giveaway.query.get_or_404(id)
    action = request.form.get("action")

    if action == "activate" and giveaway.status == "draft":
        giveaway.status = "active"
        flash("Розыгрыш активирован — можно добавлять участников", "success")
    elif action == "draft" and giveaway.status == "active" and not giveaway.winners:
        giveaway.status = "draft"
        flash("Розыгрыш возвращён в черновик", "success")
    elif action == "delete":
        db.session.delete(giveaway)
        db.session.commit()
        flash("Розыгрыш удалён", "success")
        return redirect(url_for("main.index"))

    db.session.commit()
    return redirect(url_for("main.giveaway_detail", id=id))


@bp.route("/giveaway/<int:id>/prize", methods=["POST"])
def add_prize(id):
    giveaway = Giveaway.query.get_or_404(id)
    if giveaway.status == "completed":
        flash("Нельзя добавлять призы в завершённый розыгрыш", "error")
        return redirect(url_for("main.giveaway_detail", id=id))

    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    try:
        quantity = max(1, int(request.form.get("quantity", 1)))
    except ValueError:
        quantity = 1

    if not name:
        flash("Укажите название приза", "error")
        return redirect(url_for("main.giveaway_detail", id=id))

    prize = Prize(
        giveaway_id=giveaway.id,
        name=name,
        description=description,
        quantity=quantity,
        sort_order=len(giveaway.prizes),
    )
    db.session.add(prize)
    db.session.commit()
    flash(f"Приз «{name}» добавлен", "success")
    return redirect(url_for("main.giveaway_detail", id=id))


@bp.route("/giveaway/<int:gid>/prize/<int:pid>/delete", methods=["POST"])
def delete_prize(gid, pid):
    giveaway = Giveaway.query.get_or_404(gid)
    if giveaway.status == "completed":
        flash("Нельзя удалять призы", "error")
        return redirect(url_for("main.giveaway_detail", id=gid))

    prize = Prize.query.filter_by(id=pid, giveaway_id=gid).first_or_404()
    db.session.delete(prize)
    db.session.commit()
    flash("Приз удалён", "success")
    return redirect(url_for("main.giveaway_detail", id=gid))


@bp.route("/giveaway/<int:id>/participant", methods=["POST"])
def add_participant(id):
    giveaway = Giveaway.query.get_or_404(id)
    if giveaway.status != "active":
        flash("Участников можно добавлять только в активный розыгрыш", "error")
        return redirect(url_for("main.giveaway_detail", id=id))

    name = request.form.get("name", "").strip()
    contact = request.form.get("contact", "").strip()
    try:
        participant = register_participant(giveaway, name, contact)
        flash(f"Участник {participant.name} зарегистрирован. Билет: {participant.ticket_code}", "success")
    except ValueError as e:
        flash(str(e), "error")
    return redirect(url_for("main.giveaway_detail", id=id))


@bp.route("/r/<token>", methods=["GET", "POST"])
def public_register(token):
    giveaway = Giveaway.query.filter_by(public_token=token).first_or_404()

    if request.method == "POST":
        if giveaway.status != "active":
            return render_template(
                "public_register.html",
                giveaway=giveaway,
                closed=True,
                error="Регистрация закрыта",
            )
        try:
            participant = register_participant(
                giveaway,
                request.form.get("name", ""),
                request.form.get("contact", ""),
            )
            return render_template(
                "public_register.html",
                giveaway=giveaway,
                success=True,
                participant=participant,
            )
        except ValueError as e:
            return render_template(
                "public_register.html",
                giveaway=giveaway,
                error=str(e),
                form_name=request.form.get("name", ""),
                form_contact=request.form.get("contact", ""),
            )

    return render_template(
        "public_register.html",
        giveaway=giveaway,
        closed=giveaway.status != "active",
    )


@bp.route("/giveaway/<int:gid>/participant/<int:pid>/delete", methods=["POST"])
def delete_participant(gid, pid):
    giveaway = Giveaway.query.get_or_404(gid)
    if giveaway.status == "completed":
        flash("Нельзя удалять участников", "error")
        return redirect(url_for("main.giveaway_detail", id=gid))

    participant = Participant.query.filter_by(id=pid, giveaway_id=gid).first_or_404()
    db.session.delete(participant)
    db.session.commit()
    flash("Участник удалён", "success")
    return redirect(url_for("main.giveaway_detail", id=gid))


@bp.route("/giveaway/<int:id>/draw")
def draw_page(id):
    giveaway = Giveaway.query.get_or_404(id)
    if giveaway.status == "completed":
        return redirect(url_for("main.results", id=id))
    return render_template("draw.html", giveaway=giveaway)


@bp.route("/giveaway/<int:id>/draw/run", methods=["POST"])
def execute_draw(id):
    giveaway = Giveaway.query.get_or_404(id)
    wants_json = request.accept_mimetypes.best_match(["application/json", "text/html"]) == "application/json"

    try:
        winners = run_draw(giveaway)
        first = winners[0]
        if wants_json:
            return jsonify(
                {
                    "ok": True,
                    "first_winner": first.participant.name,
                    "first_prize": first.prize.name,
                    "results_url": url_for("main.results", id=id),
                }
            )
        flash(f"Розыгрыш завершён! Победителей: {len(winners)}", "success")
        return redirect(url_for("main.results", id=id))
    except ValueError as e:
        if wants_json:
            return jsonify({"ok": False, "error": str(e)}), 400
        flash(str(e), "error")
        return redirect(url_for("main.draw_page", id=id))


@bp.route("/giveaway/<int:id>/results")
def results(id):
    giveaway = Giveaway.query.get_or_404(id)
    winners = (
        Winner.query.filter_by(giveaway_id=id)
        .order_by(Winner.place)
        .all()
    )
    return render_template("results.html", giveaway=giveaway, winners=winners)
