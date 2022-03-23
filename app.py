from flask import Flask,request,jsonify
import os
import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.automap import automap_base
from azure.storage.blob import BlobServiceClient
from key import key
import hashlib

connect_str=os.getenv("AZURE_STORAGE_CONNECTION_STRING")
container_name="bookphotos"

blob_service_client= BlobServiceClient.from_connection_string(conn_str=connect_str)

try:
    container_client=blob_service_client.get_container_client(container=container_name)
    container_client.get_container_properties()
except Exception as e:
    container_client=blob_service_client.create_container(container_name)


app=Flask(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = key
db=SQLAlchemy(app)

Base = automap_base()
Base.prepare(db.engine,reflect=True)
Accounts = Base.classes.accounts
BookDetails=Base.classes.book_details
RelatedCourses=Base.classes.related_courses
BookImages=Base.classes.book_images
PlaceOrder=Base.classes.place_order

@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
  return response

@app.route('/add_user',methods=['POST'])
def add_user():
    data=request.get_json()
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
    image=request.files['file']
    data_form=json.loads(request.form.get('data'))
    bookType=data_form['BookType']['value']

    addBook=BookDetails(id_user=data_form['userId'],book_name=data_form['BookName'],\
    book_type=bookType,book_cost=data_form['Cost'],book_author=data_form['BookAuthor'],book_description=data_form['Description'])

    db.session.add(addBook)
    db.session.commit()

    bookId=addBook.book_id
    try:
        bookImageName="book_"+str(data_form['userId'])+"_"+str(bookId)+'.jpg'
        for i in range(1,data_form['numCourses']+1):
            print(i)
            str_code="course_code_"+str(i)
            str_dept="course_dept_"+str(i)
            str_name="course_name_"+str(i)
            
            addRelevantCourse=RelatedCourses(book_id=bookId,relevant_course_code=data_form[str_code],\
            course_department=data_form[str_dept]['value'],relevant_course_name=data_form[str_name])
            db.session.add(addRelevantCourse)
        
        try:
            container_client.upload_blob(bookImageName,image)
        except Exception as e:
            print(e)
            print('error')
            
        bookImage=BookImages(book_id=bookId,image_name=bookImageName)
        db.session.add(bookImage)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.delete(addBook)
        db.session.commit()

    return jsonify({'bookId':bookId})

@app.route('/bookexchange',methods=['GET'])
def getBooks():
    ret=[]
    req=db.session.query(BookDetails).limit(20).all()
    for book in req:
        currBookDetails={}
        currBookDetails['book_id']=book.book_id
        currBookDetails['user_id']=book.id_user
        currBookDetails['book_name']=book.book_name
        currBookDetails['book_type']=book.book_type
        currBookDetails['book_cost']=book.book_cost
        currBookDetails['description']=book.book_description
        currBookDetails['book_author']=book.book_author
        relatedCourseArr=db.session.query(RelatedCourses).filter_by(book_id=book.book_id).all()
        arr=[]
        for c in relatedCourseArr:
            arr.append({'course_code':c.relevant_course_code,'course_name':c.relevant_course_name,'course_department':c.course_department})
        currBookDetails['related_courses']=arr
        img=db.session.query(BookImages).filter_by(book_id=book.book_id).first()
        imgName=img.image_name
        blob_client=container_client.get_blob_client(blob=imgName)
        currBookDetails['image_link']=blob_client.url
        ret.append(currBookDetails)
    return jsonify(ret),201

@app.route('/bookexchange/<id>',methods=['GET'])
def getBook(id):
    book=db.session.query(BookDetails).filter_by(book_id=id).first()
    print(book)
    currBookDetails={}
    currBookDetails={}
    currBookDetails['book_id']=book.book_id
    currBookDetails['user_id']=book.id_user
    currBookDetails['book_name']=book.book_name
    currBookDetails['book_type']=book.book_type
    currBookDetails['book_cost']=book.book_cost
    currBookDetails['description']=book.book_description
    currBookDetails['book_author']=book.book_author
    relatedCourseArr=db.session.query(RelatedCourses).filter_by(book_id=book.book_id).all()
    arr=[]
    for c in relatedCourseArr:
        arr.append({'course_code':c.relevant_course_code,'course_name':c.relevant_course_name,'course_department':c.course_department})
    currBookDetails['related_courses']=arr
    img=db.session.query(BookImages).filter_by(book_id=book.book_id).first()
    imgName=img.image_name
    blob_client=container_client.get_blob_client(blob=imgName)
    currBookDetails['image_link']=blob_client.url
    return jsonify(currBookDetails),201

@app.route('/bookdelete/<id>',methods=['DELETE'])
def deleteBook(id):
    curr_book_img=db.session.query(BookImages).filter_by(book_id=id).first()
    db.session.delete(curr_book_img)
    curr_book_courses=db.session.query(RelatedCourses).filter_by(book_id=id).all()
    for course in curr_book_courses:
        db.session.delete(course)
    curr_book=db.session.query(BookDetails).filter_by(book_id=id).first()
    db.session.delete(curr_book)
    db.session.commit()
    return jsonify({'deleted':id}),200

@app.route('/getbook',methods=['POST'])
def getbook():
    user_placing_order=request.args.get('user')
    book_id=request.args.get('book')
    # print(user_id)
    # print(book_id)
    curr_book=db.session.query(BookDetails).filter_by(book_id=book_id).first()
    user_taking_order=curr_book.id_user
    order=PlaceOrder(user_placing_order=user_placing_order,book_id=book_id,user_taking_order=user_taking_order)
    db.session.add(order)
    db.session.commit()
    return "done",200

@app.route('/orders',methods=['GET'])
def orders():
    user_placing_order=request.args.get('user')
    print(user_placing_order)
    orders=db.session.query(PlaceOrder).filter_by(user_placing_order=user_placing_order).limit(20).all()
    ret=[]
    for order in orders:
        book=db.session.query(BookDetails).filter_by(book_id=order.book_id).first()
        currBookDetails={}
        currBookDetails['book_id']=book.book_id
        currBookDetails['user_id']=book.id_user
        currBookDetails['book_name']=book.book_name
        currBookDetails['book_type']=book.book_type
        currBookDetails['book_cost']=book.book_cost
        currBookDetails['description']=book.book_description
        currBookDetails['book_author']=book.book_author
        relatedCourseArr=db.session.query(RelatedCourses).filter_by(book_id=book.book_id).all()
        arr=[]
        for c in relatedCourseArr:
            arr.append({'course_code':c.relevant_course_code,'course_name':c.relevant_course_name,'course_department':c.course_department})
        currBookDetails['related_courses']=arr
        img=db.session.query(BookImages).filter_by(book_id=book.book_id).first()
        imgName=img.image_name
        blob_client=container_client.get_blob_client(blob=imgName)
        currBookDetails['image_link']=blob_client.url
        ret.append(currBookDetails)
    return jsonify(ret),201

@app.route('/lenders',methods=['GET'])
def lenders():
    user_taking_order=request.args.get('user')
    print(user_taking_order)
    orders=db.session.query(PlaceOrder).filter_by(user_taking_order=user_taking_order).limit(20).all()
    ret=[]
    for order in orders:
        book=db.session.query(BookDetails).filter_by(book_id=order.book_id).first()
        currBookDetails={}
        currBookDetails['book_id']=book.book_id
        currBookDetails['user_id']=book.id_user
        currBookDetails['book_name']=book.book_name
        currBookDetails['book_type']=book.book_type
        currBookDetails['book_cost']=book.book_cost
        currBookDetails['description']=book.book_description
        currBookDetails['book_author']=book.book_author
        relatedCourseArr=db.session.query(RelatedCourses).filter_by(book_id=book.book_id).all()
        arr=[]
        for c in relatedCourseArr:
            arr.append({'course_code':c.relevant_course_code,'course_name':c.relevant_course_name,'course_department':c.course_department})
        currBookDetails['related_courses']=arr
        img=db.session.query(BookImages).filter_by(book_id=book.book_id).first()
        imgName=img.image_name
        blob_client=container_client.get_blob_client(blob=imgName)
        currBookDetails['image_link']=blob_client.url
        ret.append(currBookDetails)
    return jsonify(ret),201

    
if __name__=="__main__":
    app.run(debug=True)