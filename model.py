from mongoengine import *


# can add max_length
class WorkExperience(EmbeddedDocument):
    position = StringField(required=True)
    start_date = DateTimeField()
    end_date = DateTimeField()
    company_description = StringField()
    company_name = StringField()
    job_description = StringField()


class User(Document):
    title = StringField(required=True)
    fullname = StringField(required=True)
    cv_url = StringField(required=True)
    age = StringField(required=True)
    updated_by_owner = DateTimeField(required=True)
    salary_amount = IntField()
    list_of_exp = ListField(EmbeddedDocumentField(WorkExperience))
