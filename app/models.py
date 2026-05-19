from datetime import datetime

from app import db


class Giveaway(db.Model):
    __tablename__ = "giveaways"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    status = db.Column(db.String(20), default="draft")  # draft | active | completed
    public_token = db.Column(db.String(32), unique=True, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    drawn_at = db.Column(db.DateTime, nullable=True)

    prizes = db.relationship("Prize", backref="giveaway", cascade="all, delete-orphan", lazy=True)
    participants = db.relationship(
        "Participant", backref="giveaway", cascade="all, delete-orphan", lazy=True
    )
    winners = db.relationship("Winner", backref="giveaway", cascade="all, delete-orphan", lazy=True)

    @property
    def prize_slots(self):
        return sum(p.quantity for p in self.prizes)

    @property
    def can_draw(self):
        return (
            self.status == "active"
            and len(self.participants) > 0
            and self.prize_slots > 0
            and len(self.participants) >= self.prize_slots
            and not self.winners
        )


class Prize(db.Model):
    __tablename__ = "prizes"

    id = db.Column(db.Integer, primary_key=True)
    giveaway_id = db.Column(db.Integer, db.ForeignKey("giveaways.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    quantity = db.Column(db.Integer, default=1)
    sort_order = db.Column(db.Integer, default=0)


class Participant(db.Model):
    __tablename__ = "participants"

    id = db.Column(db.Integer, primary_key=True)
    giveaway_id = db.Column(db.Integer, db.ForeignKey("giveaways.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    contact = db.Column(db.String(200), default="")
    ticket_code = db.Column(db.String(32), unique=True, nullable=False)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)


class Winner(db.Model):
    __tablename__ = "winners"

    id = db.Column(db.Integer, primary_key=True)
    giveaway_id = db.Column(db.Integer, db.ForeignKey("giveaways.id"), nullable=False)
    prize_id = db.Column(db.Integer, db.ForeignKey("prizes.id"), nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey("participants.id"), nullable=False)
    drawn_at = db.Column(db.DateTime, default=datetime.utcnow)
    place = db.Column(db.Integer, default=1)

    prize = db.relationship("Prize")
    participant = db.relationship("Participant")
