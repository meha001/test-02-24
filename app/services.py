import random
import secrets
import string
from datetime import datetime

from app import db
from app.models import Giveaway, Participant, Prize, Winner


def generate_ticket_code(length=8):
    alphabet = string.ascii_uppercase + string.digits
    while True:
        code = "".join(secrets.choice(alphabet) for _ in range(length))
        if not Participant.query.filter_by(ticket_code=code).first():
            return code


def generate_public_token(length=16):
    alphabet = string.ascii_lowercase + string.digits
    while True:
        token = "".join(secrets.choice(alphabet) for _ in range(length))
        if not Giveaway.query.filter_by(public_token=token).first():
            return token


def ensure_public_token(giveaway: Giveaway):
    if not giveaway.public_token:
        giveaway.public_token = generate_public_token()


def register_participant(giveaway: Giveaway, name: str, contact: str = ""):
    if giveaway.status != "active":
        raise ValueError("Регистрация на этот розыгрыш сейчас закрыта")

    name = name.strip()
    contact = contact.strip()
    if not name:
        raise ValueError("Укажите ваше имя")

    if contact:
        existing = Participant.query.filter_by(giveaway_id=giveaway.id, contact=contact).first()
        if existing:
            raise ValueError("Этот контакт уже зарегистрирован в розыгрыше")

    participant = Participant(
        giveaway_id=giveaway.id,
        name=name,
        contact=contact,
        ticket_code=generate_ticket_code(),
    )
    db.session.add(participant)
    db.session.commit()
    return participant


def run_draw(giveaway: Giveaway):
    if not giveaway.can_draw:
        raise ValueError("Розыгрыш нельзя провести в текущем состоянии")

    prizes_expanded = []
    for prize in sorted(giveaway.prizes, key=lambda p: (p.sort_order, p.id)):
        prizes_expanded.extend([prize] * prize.quantity)

    pool = list(giveaway.participants)
    random.shuffle(pool)

    winners = []
    for place, (prize, participant) in enumerate(zip(prizes_expanded, pool), start=1):
        winner = Winner(
            giveaway_id=giveaway.id,
            prize_id=prize.id,
            participant_id=participant.id,
            place=place,
        )
        db.session.add(winner)
        winners.append(winner)

    giveaway.status = "completed"
    giveaway.drawn_at = datetime.utcnow()
    db.session.commit()
    return winners
