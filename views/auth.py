from flask import request, jsonify, Blueprint
import hashlib
from db import db
from dbmodels import *

auth = Blueprint('auth', __name__)


@auth.route('/add_user', methods=['POST'])
def add_user():
    data = request.get_json()
    res = db.session.query(Accounts).filter_by(
        username=data['username']).first()
    if res is not None:
        return jsonify({'username': 'exists'})
    res = db.session.query(Accounts).filter_by(
        email_id=data['email_id']).first()
    if res is not None:
        return jsonify({'email_id': 'exists'})
    pas = hashlib.sha256(data['password'].encode())
    addAcc = Accounts(
        username=data['username'], email_id=data['email_id'], password=pas.hexdigest())
    db.session.add(addAcc)
    db.session.commit()
    return jsonify({'userId': addAcc.id_user})


@auth.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    res = db.session.query(Accounts).filter_by(
        email_id=data['email_id']).first()
    if res is None:
        return jsonify({'email_id': 'does not exist'})
    pas = hashlib.sha256(data['password'].encode())
    if res.password != pas.hexdigest():
        return jsonify({'password': 'does not match'})
    return jsonify({'userId': res.id_user})
