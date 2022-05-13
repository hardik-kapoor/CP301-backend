from sqlalchemy.ext.automap import automap_base
from sqlalchemy import create_engine
import os
from db import db

Base = automap_base()
engine = create_engine(os.getenv('POSTGRES_CONNECTION_STRING'))
Base.prepare(engine, reflect=True)
Accounts = Base.classes.accounts
BookDetails = Base.classes.book_details
RelatedCourses = Base.classes.related_courses
BookImages = Base.classes.book_images
PlaceOrder = Base.classes.place_order
AccountDetails = Base.classes.account_details
