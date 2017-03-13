import settings
from mongoengine import connect

class MongoCon(object):
    isconn = False

    @classmethod
    def get_connection(cls):

        #Create the connection to database
        if not cls.isconn:
            connect(settings.MONGODB_NAME,
                    username=settings.MONGODB_USER,
                    password=settings.MONGODB_PASS,
                    host=settings.MONGODB_HOST)

            isconn = True


dbcon=MongoCon()
dbcon.get_connection()
