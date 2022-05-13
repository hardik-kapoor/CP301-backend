from locale import currency
from flask import request, jsonify, Blueprint
import json
from db import db
from dbmodels import *
from googleStorage.images import bucket
from sqlalchemy.sql.operators import ilike_op
from sqlalchemy import text

bookExchange = Blueprint('bookExchange', __name__)


@bookExchange.route('/bookcreate', methods=['POST'])
def bookcreate():
    image = request.files['file']
    data_form = json.loads(request.form.get('data'))
    bookType = data_form['BookType']['value']

    addBook = BookDetails(id_user=data_form['userId'], book_name=data_form['BookName'],
                          book_type=bookType, book_cost=data_form['Cost'], book_author=data_form['BookAuthor'], book_description=data_form['Description'], status='NOT_SOLD')

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
            blob = bucket.blob(bookImageName)
            blob.upload_from_string(
                image.read(),
                content_type=image.content_type
            )
        except Exception as e:
            print(e)
            print('error')

        bookImage = BookImages(book_id=bookId, image_name=bookImageName,image_link=blob.public_url)
        db.session.add(bookImage)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.delete(addBook)
        db.session.commit()

    return jsonify({'bookId': bookId})


@bookExchange.route('/bookexchange', methods=['GET'])
def getBooks():
    course = request.args.get("course")
    dept = request.args.get("dept")
    if type(dept) == str:
        dept = dept.split(',')
    typ = request.args.get("type")
    if type(typ) == str:
        typ = typ.split(',')
    if course == '' or course is None:
        req = db.session.query(BookDetails).outerjoin(
            RelatedCourses, BookDetails.book_id == RelatedCourses.book_id)
    else:
        req = db.session.query(BookDetails).join(RelatedCourses, BookDetails.book_id == RelatedCourses.book_id).filter(
            ilike_op(RelatedCourses.relevant_course_code, course))
    if dept == [''] or dept is None:
        pass
    else:
        for d in dept:
            req = req.filter(RelatedCourses.course_department == d)
    if typ == [''] or typ is None:
        pass
    else:
        for t in typ:
            req = req.filter(BookDetails.book_type == t)
    ret = []
    for book in req:
        currBookDetails = {}
        currBookDetails['book_id'] = book.book_id
        currBookDetails['user_id'] = book.id_user
        currBookDetails['book_name'] = book.book_name
        currBookDetails['book_type'] = book.book_type
        currBookDetails['book_cost'] = book.book_cost
        currBookDetails['description'] = book.book_description
        currBookDetails['book_author'] = book.book_author
        currBookDetails['status'] = book.status
        relatedCourseArr = db.session.query(
            RelatedCourses).filter_by(book_id=book.book_id).all()
        arr = []
        for c in relatedCourseArr:
            arr.append({'course_code': c.relevant_course_code,
                       'course_name': c.relevant_course_name, 'course_department': c.course_department})
        currBookDetails['related_courses'] = arr
        img = db.session.query(BookImages).filter_by(
            book_id=book.book_id).first()
        imgName = img.image_link
        print(imgName)
        # blob_client = container_client.get_blob_client(blob=imgName)
        currBookDetails['image_link'] = imgName
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
    currBookDetails['status'] = book.status
    relatedCourseArr = db.session.query(
        RelatedCourses).filter_by(book_id=book.book_id).all()
    arr = []
    for c in relatedCourseArr:
        arr.append({'course_code': c.relevant_course_code,
                   'course_name': c.relevant_course_name, 'course_department': c.course_department})
    currBookDetails['related_courses'] = arr
    img = db.session.query(BookImages).filter_by(book_id=book.book_id).first()
    imgName = img.image_link
    # blob_client = container_client.get_blob_client(blob=imgName)
    currBookDetails['image_link'] = imgName
    return jsonify(currBookDetails), 201


@bookExchange.route('/bookdelete/<id>', methods=['DELETE'])
def deleteBook(id):
    curr_book_img = db.session.query(BookImages).filter_by(book_id=id).first()
    # container_client.delete_blob(curr_book_img.image_name)
    blob=bucket.blob(curr_book_img.image_name)
    blob.delete()
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
                       book_id=book_id, user_taking_order=user_taking_order, status='NOT_CHECKED')
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
        currBookDetails['status'] = book.status
        relatedCourseArr = db.session.query(
            RelatedCourses).filter_by(book_id=book.book_id).all()
        arr = []
        for c in relatedCourseArr:
            arr.append({'course_code': c.relevant_course_code,
                       'course_name': c.relevant_course_name, 'course_department': c.course_department})
        currBookDetails['related_courses'] = arr
        img = db.session.query(BookImages).filter_by(
            book_id=book.book_id).first()
        imgName = img.image_link
        currBookDetails['image_link'] = imgName
        currBookDetails['status'] = order.status
        ret.append(currBookDetails)
    return jsonify(ret), 201


# @bookExchange.route('/lenders', methods=['GET'])
# def lenders():
#     user_taking_order = request.args.get('user')
#     # print(user_taking_order)
#     orders = db.session.query(PlaceOrder).filter_by(
#         user_taking_order=user_taking_order).limit(20).all()
#     ret = []
#     for order in orders:
#         book = db.session.query(BookDetails).filter_by(
#             book_id=order.book_id).first()
#         currBookDetails = {}
#         currBookDetails['book_id'] = book.book_id
#         currBookDetails['user_id'] = book.id_user
#         currBookDetails['book_name'] = book.book_name
#         currBookDetails['book_type'] = book.book_type
#         currBookDetails['book_cost'] = book.book_cost
#         currBookDetails['description'] = book.book_description
#         currBookDetails['book_author'] = book.book_author
#         relatedCourseArr = db.session.query(
#             RelatedCourses).filter_by(book_id=book.book_id).all()
#         arr = []
#         for c in relatedCourseArr:
#             arr.append({'course_code': c.relevant_course_code,
#                        'course_name': c.relevant_course_name, 'course_department': c.course_department})
#         currBookDetails['related_courses'] = arr
#         img = db.session.query(BookImages).filter_by(
#             book_id=book.book_id).first()
#         imgName = img.image_name
#         blob_client = container_client.get_blob_client(blob=imgName)
#         currBookDetails['image_link'] = blob_client.url
#         currBookDetails['user_id']=order.user_placing_order
#         user=db.session.query(Accounts).filter_by(id_user=order.user_placing_order).first()
#         currBookDetails['user_username']=user.username
#         currBookDetails['user_email_id']=user.email_id
#         ret.append(currBookDetails)
#     return jsonify(ret), 201

@bookExchange.route('/lenders', methods=['GET'])
def lenders():
    user_taking_order = request.args.get('user')
    # print(user_taking_order)
    books = db.session.query(BookDetails).filter_by(
        id_user=user_taking_order).limit(20).all()
    ret = []
    for book in books:
        orders = db.session.query(PlaceOrder).filter_by(
            user_taking_order=user_taking_order, book_id=book.book_id).all()
        currBookDetails = {}
        currBookDetails['book_id'] = book.book_id
        currBookDetails['user_id'] = book.id_user
        currBookDetails['book_name'] = book.book_name
        currBookDetails['book_type'] = book.book_type
        currBookDetails['book_cost'] = book.book_cost
        currBookDetails['description'] = book.book_description
        currBookDetails['book_author'] = book.book_author
        currBookDetails['status'] = book.status
        relatedCourseArr = db.session.query(
            RelatedCourses).filter_by(book_id=book.book_id).all()
        arr = []
        for c in relatedCourseArr:
            arr.append({'course_code': c.relevant_course_code,
                       'course_name': c.relevant_course_name, 'course_department': c.course_department})
        currBookDetails['related_courses'] = arr
        img = db.session.query(BookImages).filter_by(
            book_id=book.book_id).first()
        imgName = img.image_link
        currBookDetails['image_link'] = imgName
        currBookDetails['Orders'] = []
        for order in orders:
            user = db.session.query(Accounts).filter_by(
                id_user=order.user_placing_order).first()
            currBookDetails['Orders'].append(
                {'username': user.username, 'email_id': user.email_id, 'user_id': user.id_user, 'status': order.status})
        ret.append(currBookDetails)
    return jsonify(ret), 201


@bookExchange.route('/orderdelete', methods=['DELETE'])
def orderDel():
    user_placing_order = request.args.get('user')
    book_of_order = request.args.get('bookid')
    curr_order = db.session.query(PlaceOrder).filter_by(
        book_id=book_of_order, user_placing_order=user_placing_order).first()
    db.session.delete(curr_order)
    db.session.commit()
    return jsonify({'deleted': book_of_order}), 200


@bookExchange.route('/orderConfirm/<user_placing_order>/<user_taking_order>/<book_id>', methods=['PATCH'])
def orderConfirm(user_placing_order,user_taking_order,book_id):
    print(user_placing_order,book_id)
    db.session.query(PlaceOrder).filter(PlaceOrder.user_taking_order == user_taking_order , PlaceOrder.book_id ==
                                           book_id , PlaceOrder.user_placing_order != user_placing_order).update({PlaceOrder.status: 'REJECTED'})
    db.session.query(PlaceOrder).filter(PlaceOrder.user_taking_order == user_taking_order , PlaceOrder.book_id ==
                                           book_id , PlaceOrder.user_placing_order == user_placing_order).update({PlaceOrder.status: 'ACCEPTED'})
    db.session.query(BookDetails).filter(
        BookDetails.book_id == book_id).update({BookDetails.status: 'SOLD'})
    db.session.commit()
    return 'done', 201
