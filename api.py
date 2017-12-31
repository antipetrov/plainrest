#!/usr/bin/env python
# -*- coding: utf-8 -*-

import abc
import json
import datetime
import logging
import hashlib
import uuid
from datetime import datetime, timedelta
from optparse import OptionParser
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler

import scoring

SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}

class FieldValidationError(Exception):
    def __init__(self, message):
        super(FieldValidationError, self).__init__(message)
        self.field = None

class ValidationError(Exception):
    def __init__(self, message, field=None):
        super(ValidationError, self).__init__(message)
        self.field = field

class Field(object):
    def __init__(self, required=False, nullable=True):
        self.required = required
        self.nullable = nullable

        self.value = None

    def __set__(self, obj, value):
        self.value = self.validate(value)
    

    def __get__(self, obj, type=None):
        return self.value

    def _field_error(self, message):
        message = "%s: %s" % (self.__class__.__name__, message)
        return FieldValidationError(message)

    def validate(self, value):

        if not self.nullable and value == None:
            raise self._field_error('cannot be None')

        return value


class CharField(Field):

    def validate(self, value):
        value = super(CharField, self).validate(value) 

        if value and not isinstance(value, str):
            raise self._field_error('must be string')

        return value

class ArgumentsField(Field):
    def validate(self, value):
        value = super(ArgumentsField, self).validate(value)

        if value and (not value ==None and not isinstance(value, dict)):
            raise self._field_error('needs to be dict')

        return value

class EmailField(CharField):

    def validate(self, value):
        value = super(EmailField, self).validate(value)

        if value and value.find('@') == -1:
            raise self._field_error('invalid email')


        return value

class PhoneField(Field):
    def validate(self, value):
        value = super(PhoneField, self).validate(value)

        if value and (not value.startswith('7') or not len(value)==11):
            raise self._field_error('invalid phone')

        return value


class DateField(Field):
    
    def validate(self, value):
        value = super(DateField, self).validate(value)

        if value:
            try:
                value = datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                raise self._field_error('invalid date')

        return value


class BirthDayField(DateField):

    def validate(self, value):
        value = super(BirthDayField, self).validate(value)

        if value:
            if datetime.now().year - value.year > 70:
                raise self._field_error('invalid birth date (age must be <= 70)')

        return value


class IntField(Field):
    def validate(self, value):
        value = super(IntField, self).validate(value)

        if value:
            try:
                value = int(value)
            except ValueError:
                raise self._field_error('is not integer')

        return value


class GenderField(IntField):

    def validate(self, value):
        value = super(GenderField, self).validate(value)
        
        if value:
            if not int(value) in GENDERS.keys():
                raise self._field_error('invalid gender (must be 0,1 or 2)')

        return value

       
class ClientIDsField(Field):

    def validate(self, value):
        value = super(ClientIDsField, self).validate(value)

        if value:
            if not isinstance(value, list):
                raise self._field_error('not list')

            for i, v in enumerate(value):
                try:
                    value[i] = int(v)
                except ValueError:
                    raise self._field_error('values must be integers')

        print('int list', value)

        return value

class ApiRequest(object):
    
    def __init__(self, fields):
        self.fields = {k:v for k,v in self.__class__.__dict__.iteritems() if issubclass(v.__class__, Field)}

        for k,v in self.fields.iteritems():
            try:
                print('assign ', k, fields.get(k, None))
                self.__setattr__(k, fields.get(k, None)) # field vailues get validated here
            except FieldValidationError as e:
                raise ValidationError(message=e.message, field=k)

        # run request-wide validation
        self.validate()

    def __str__(self):
        return "<ApiRequest %s fields: >" % (self.__class__.__name__, " ".join(["%s:%s"%(k,v) for k,v in self.fields.iteritems()]))

    def validate(self):
        raise NotImplementedError()

    def process(self):
        raise NotImplementedError()

class ClientsInterestsRequest(ApiRequest):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    def validate(self):
        return self

    def process(self):
        result = {}
        for cid in self.client_ids:
            result[cid] = scoring.get_interests(None, cid)


        return result


class OnlineScoreRequest(ApiRequest):
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False)
    gender = GenderField(required=False, nullable=True)

    def validate(self):

        if (self.email and self.phone) or \
           (self.first_name and self.last_name) or \
           (self.birthday and self.gender):
           return self

        else:
            raise ValidationError('One of pairs (phone, email) or '
                                  '(first_name, last_name) or '
                                  '(birthday, gender) needs to be passed')

        # if not self.first_name and not self.last_name:
        #     raise ValidationError('first name or last name required')

        # if not self.birthday and not self.gender:
        #     raise ValidationError('birthdate or gender required')



    def process(self):
        score = scoring.get_score(None, 
                                  self.phone, 
                                  self.email, 
                                  self.birthday,
                                  self.gender, 
                                  self.first_name, 
                                  self.last_name)

        return  {"score": score}




class MethodRequest(ApiRequest):

    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)


    __method_handlers__ = {
        'online_score': OnlineScoreRequest,
        'client_instrests': ClientsInterestsRequest,
    }

    def __init__(self, fields):
        self.handler_class = None
        super(MethodRequest, self).__init__(fields)
        
    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN

    def __str__(self):
        return "<request %s(%s) auth=%s:%s>" % (self.method, json.dumps(self.arguments), self.login, self.token)

    def validate(self):
        try:
            self.handler_class = self.__method_handlers__[self.method]
        except KeyError as e:
            raise ValidationError('Method "%s" not found' % self.method)

        return self

    def process(self):
        return self.handler_class(self.arguments).process()


def check_auth(request):
    if request.login == ADMIN_LOGIN:
        digest = hashlib.sha512(datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):

    try:
        api_request = MethodRequest(request)
        response = api_request.process()
        code = 200
    except ValidationError as e:
        if e.field:
            error = 'field "%s" error: %s'%(e.field, e.message)
        else:
            error = e.message

        code = INVALID_REQUEST
        response = {'error':error}

    #todo: update ctx - has
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, self.store)
                except Exception, e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {"response": response, "code": code}
        else:
            r = {"error": response or ERRORS.get(code, "Unknown Error"), "code": code}
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return

if __name__ == "__main__":
    op = OptionParser()
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
