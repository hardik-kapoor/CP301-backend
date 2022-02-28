from flask import Flask,request,jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.automap import automap_base

app=Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://lzlfnbkgtjnrtk:ed4a038530d897e4fabe8810580787d371f00dec2fee9c707b11e9fdbfb2704b@ec2-54-209-221-231.compute-1.amazonaws.com/d56ehg9cnhk4l8'
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

@app.route('/')
def index():
    return "<h1>hello</h1>"

@app.route('/check')
def check():
    res=db.session.query(Accounts).where()
    print(res)
    return ""

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
    addAcc=Accounts(username=data['username'],email_id=data['email_id'],password=data['password'])
    db.session.add(addAcc)
    db.session.commit()
    return jsonify({'userId':addAcc.id_user})

@app.route('/login',methods=['POST'])
def login():
    data=request.get_json()
    res=db.session.query(Accounts).filter_by(email_id=data['email_id']).first()
    if res is None:
        return jsonify({'email_id':'does not exist'})
    if res.password != data['password']:
        return jsonify({'password':'does not match'})
    return jsonify({'userId':res.id_user})

if __name__=="__main__":
    app.run(debug=True)