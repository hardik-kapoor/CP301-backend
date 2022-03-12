from flask import Flask,request,jsonify
import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.automap import automap_base
from key import key
import hashlib

app=Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = key
db=SQLAlchemy(app)

Base = automap_base()
Base.prepare(db.engine,reflect=True)
Accounts = Base.classes.accounts

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response

@app.route('/add_user',methods=['POST'])
def add_user():
    data=request.get_json()
    # print(data['username'])
    # print(data)
    res=db.session.query(Accounts).filter_by(username=data['username']).first()
    if res is not None:
        return jsonify({'username':'exists'})
    res=db.session.query(Accounts).filter_by(email_id=data['email_id']).first()
    if res is not None:
        return jsonify({'email_id':'exists'})
    pas=hashlib.sha256(data['password'].encode())
    addAcc=Accounts(username=data['username'],email_id=data['email_id'],password=pas.hexdigest())
    db.session.add(addAcc)
    db.session.commit()
    return jsonify({'userId':addAcc.id_user})

@app.route('/login',methods=['POST'])
def login():
    data=request.get_json()
    res=db.session.query(Accounts).filter_by(email_id=data['email_id']).first()
    if res is None:
        return jsonify({'email_id':'does not exist'})
    pas=hashlib.sha256(data['password'].encode())
    if res.password != pas.hexdigest():
        return jsonify({'password':'does not match'})
    return jsonify({'userId':res.id_user})

@app.route('/bookcreate',methods=['POST'])
def bookcreate():
    data=request.files['file']
    print(data)
    data2=json.loads(request.form.get('data'))
    print(data2)
    return 'done'

if __name__=="__main__":
    app.run(debug=True)