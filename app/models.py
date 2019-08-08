from datetime import datetime
from hashlib import md5
from time import time
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

from app import app, db, login


user_fit = db.Table(
    'user_fit',
    db.Column('fitness_id', db.Integer, db.ForeignKey('fitness.id')),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'))
)


class Fitness(db.Model):
    __tablename__ = 'fitness'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    summary = db.Column(db.String(90))
    type_id = db.Column(db.Integer, db.ForeignKey('typefit.id'))
    miles = db.Column(db.Numeric(8,2))
    stats = db.Column(db.Numeric(8,2))
    minutes = db.Column(db.Numeric(8,2))
    story_fit = db.relationship('Fitstory', backref='fitness', lazy='dynamic')
    users = db.relationship("User", secondary=user_fit)
    # stars = db.relationship(
        # 'Fitness', secondary=user_fit,
        # primaryjoin=(user_fit.c.user_id == id),
        # secondaryjoin=(user_fit.c.fitness_id == id),
        # backref=db.backref('user_fit', lazy='dynamic'), lazy='dynamic')    


class Fitstory(db.Model):
    __tablename__ = 'fitstory'

    id = db.Column(db.Integer, primary_key=True)
    storydet = db.Column(db.String(990))    
    fit_id = db.Column(db.Integer, db.ForeignKey('fitness.id'))

        
class Typefit(db.Model):
    __tablename__ = 'typefit'

    id = db.Column(db.Integer, primary_key=True)
    typedet = db.Column(db.String(45))
    fitness_typefit = db.relationship('Fitness', backref = 'typefit', lazy = 'dynamic')


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<User {}>'.format(self.username) 

    def avatar(self, size):
        digest = md5(self.email.lower().encode('utf-8')).hexdigest()
        return 'https://www.gravatar.com/avatar/{}?d=identicon&s={}'.format(digest, size)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_reset_password_token(self, expires_in=600):
        return jwt.encode(
            {'reset_password': self.id, 'exp': time() + expires_in},
            app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    @staticmethod
    def verify_reset_password_token(token):
        try:
            id = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])['reset_password']
        except:
            return
        return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))
