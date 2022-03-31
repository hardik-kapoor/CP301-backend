from flask import request, jsonify, Blueprint
import json
from db import db
from dbmodels import *
from azureStorage.images import container_client
from sqlalchemy.sql.operators import ilike_op
from sqlalchemy import text

bookExchange = Blueprint('bookExchange', __name__)


@bookExchange.route('/bookcreate', methods=['POST'])
def bookcreate():
    image = request.files['file']
    data_form = json.loads(request.form.get('data'))
    bookType = data_form['BookType']['value']

    addBook = BookDetails(id_user=data_form['userId'], book_name=data_form['BookName'],
                          book_type=bookType, book_cost=data_form['Cost'], book_author=data_form['BookAuthor'], book_description=data_form['Description'])

    db.session.add(addBook)
    db.session.commit()

    bookId = addBook.book_id
    try:
        bookImageName = "book_"+str(data_form['userId'])+"_"+str(bookId)+'.jpg'
        for i in range(1, data_form['numCourses']+1):
            print(i)
            str_code = "course_code_"+str(i)
            str_dept = "course_dept_"+str(i)
            str_name = "course_name_"+str(i)

            addRelevantCourse = RelatedCourses(book_id=bookId, relevant_course_code=data_form[str_code],
                                               course_department=data_form[str_dept]['value'], relevant_course_name=data_form[str_name])
            db.session.add(addRelevantCourse)

        try:
            container_client.upload_blob(bookImageName, image)
        except Exception as e:
            print(e)
            print('error')

        bookImage = BookImages(book_id=bookId, image_name=bookImageName)
        db.session.add(bookImage)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.delete(addBook)
        db.session.commit()

    return jsonify({'bookId': bookId})


@bookExchange.route('/bookexchange', methods=['GET'])
def getBooks():
    # course=request.args.get("course")
    # dept=request.args.get("dept")
    # if type(dept)==str:
    #     dept=dept.split(',')
    # typ=request.args.get("type")
    # if type(typ)==str:
    #     typ=typ.split(',')
    # sql=text('SELECT * FROM BookDetails as b,RelatedCourses')
    # if course=='' or course is None:
    #     req=db.session.query(BookDetails).join(RelatedCourses,BookDetails.book_id==RelatedCourses.book_id,isouter=True)
    # else:
    #     req=db.session.query(BookDetails).join(RelatedCourses,BookDetails.book_id==RelatedCourses.book_id).filter(ilike_op(RelatedCourses.relevant_course_code,course))
    # if dept==[''] or dept is None:
    #     pass
    # else:
    #     for d in dept:
    #         req=req.filter(RelatedCourses.course_department==d)
    # print(req.all())
    ret = []
    # req=req.all()
    req = db.session.query(BookDetails).limit(10).all()
    for book in req:
        print(book.MetaData.keys)
        currBookDetails = {}
        currBookDetails['book_id'] = book.book_id
        currBookDetails['user_id'] = book.id_user
        currBookDetails['book_name'] = book.book_name
        currBookDetails['book_type'] = book.book_type
        currBookDetails['book_cost'] = book.book_cost
        currBookDetails['description'] = book.book_description
        currBookDetails['book_author'] = book.book_author
        relatedCourseArr = db.session.query(
            RelatedCourses).filter_by(book_id=book.book_id).all()
        arr = []
        for c in relatedCourseArr:
            arr.append({'course_code': c.relevant_course_code,
                       'course_name': c.relevant_course_name, 'course_department': c.course_department})
        currBookDetails['related_courses'] = arr
        img = db.session.query(BookImages).filter_by(
            book_id=book.book_id).first()
        imgName = img.image_name
        blob_client = container_client.get_blob_client(blob=imgName)
        currBookDetails['image_link'] = blob_client.url
        ret.append(currBookDetails)
    return jsonify(ret), 201


@bookExchange.route('/bookexchange/<id>', methods=['GET'])
def getBook(id):
    book = db.session.query(BookDetails).filter_by(book_id=id).first()
    print(book)
    currBookDetails = {}
    currBookDetails = {}
    currBookDetails['book_id'] = book.book_id
    currBookDetails['user_id'] = book.id_user
    currBookDetails['book_name'] = book.book_name
    currBookDetails['book_type'] = book.book_type
    currBookDetails['book_cost'] = book.book_cost
    currBookDetails['description'] = book.book_description
    currBookDetails['book_author'] = book.book_author
    relatedCourseArr = db.session.query(
        RelatedCourses).filter_by(book_id=book.book_id).all()
    arr = []
    for c in relatedCourseArr:
        arr.append({'course_code': c.relevant_course_code,
                   'course_name': c.relevant_course_name, 'course_department': c.course_department})
    currBookDetails['related_courses'] = arr
    img = db.session.query(BookImages).filter_by(book_id=book.book_id).first()
    imgName = img.image_name
    blob_client = container_client.get_blob_client(blob=imgName)
    currBookDetails['image_link'] = blob_client.url
    return jsonify(currBookDetails), 201


@bookExchange.route('/bookdelete/<id>', methods=['DELETE'])
def deleteBook(id):
    curr_book_img = db.session.query(BookImages).filter_by(book_id=id).first()
    container_client.delete_blob(curr_book_img.image_name)
    curr_book = db.session.query(BookDetails).filter_by(book_id=id).first()
    db.session.delete(curr_book)
    db.session.commit()
    return jsonify({'deleted': id}), 200


@bookExchange.route('/getbook', methods=['POST'])
def getbook():
    user_placing_order = request.args.get('user')
    book_id = request.args.get('book')
    curr_book = db.session.query(
        BookDetails).filter_by(book_id=book_id).first()
    user_taking_order = curr_book.id_user
    order = PlaceOrder(user_placing_order=user_placing_order,
                       book_id=book_id, user_taking_order=user_taking_order)
    db.session.add(order)
    db.session.commit()
    return "done", 200


@bookExchange.route('/orders', methods=['GET'])
def orders():
    user_placing_order = request.args.get('user')
    print(user_placing_order)
    orders = db.session.query(PlaceOrder).filter_by(
        user_placing_order=user_placing_order).limit(20).all()
    ret = []
    for order in orders:
        book = db.session.query(BookDetails).filter_by(
            book_id=order.book_id).first()
        currBookDetails = {}
        currBookDetails['book_id'] = book.book_id
        currBookDetails['user_id'] = book.id_user
        currBookDetails['book_name'] = book.book_name
        currBookDetails['book_type'] = book.book_type
        currBookDetails['book_cost'] = book.book_cost
        currBookDetails['description'] = book.book_description
        currBookDetails['book_author'] = book.book_author
        relatedCourseArr = db.session.query(
            RelatedCourses).filter_by(book_id=book.book_id).all()
        arr = []
        for c in relatedCourseArr:
            arr.append({'course_code': c.relevant_course_code,
                       'course_name': c.relevant_course_name, 'course_department': c.course_department})
        currBookDetails['related_courses'] = arr
        img = db.session.query(BookImages).filter_by(
            book_id=book.book_id).first()
        imgName = img.image_name
        blob_client = container_client.get_blob_client(blob=imgName)
        currBookDetails['image_link'] = blob_client.url
        ret.append(currBookDetails)
    return jsonify(ret), 201


@bookExchange.route('/lenders', methods=['GET'])
def lenders():
    user_taking_order = request.args.get('user')
    print(user_taking_order)
    orders = db.session.query(PlaceOrder).filter_by(
        user_taking_order=user_taking_order).limit(20).all()
    ret = []
    for order in orders:
        book = db.session.query(BookDetails).filter_by(
            book_id=order.book_id).first()
        currBookDetails = {}
        currBookDetails['book_id'] = book.book_id
        currBookDetails['user_id'] = book.id_user
        currBookDetails['book_name'] = book.book_name
        currBookDetails['book_type'] = book.book_type
        currBookDetails['book_cost'] = book.book_cost
        currBookDetails['description'] = book.book_description
        currBookDetails['book_author'] = book.book_author
        relatedCourseArr = db.session.query(
            RelatedCourses).filter_by(book_id=book.book_id).all()
        arr = []
        for c in relatedCourseArr:
            arr.append({'course_code': c.relevant_course_code,
                       'course_name': c.relevant_course_name, 'course_department': c.course_department})
        currBookDetails['related_courses'] = arr
        img = db.session.query(BookImages).filter_by(
            book_id=book.book_id).first()
        imgName = img.image_name
        blob_client = container_client.get_blob_client(blob=imgName)
        currBookDetails['image_link'] = blob_client.url
        ret.append(currBookDetails)
    return jsonify(ret), 201
