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
import store

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


class AuthError(Exception):
    pass


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
        message = "%s %s" % (self.__class__.__name__, message)
        return FieldValidationError(message)

    def validate(self, value):
        if not self.nullable and value == None:
            raise self._field_error('cannot be None')

        return value


class CharField(Field):

    def validate(self, value):
        value = super(CharField, self).validate(value)

        if not value==None and type(value) in (dict, list, tuple):
            raise self._field_error('must be string')

        return value

class ArgumentsField(Field):

    def validate(self, value):
        value = super(ArgumentsField, self).validate(value)

        if not value==None and not isinstance(value, dict):
            raise self._field_error('needs to be dict')

        return value

class EmailField(CharField):

    def validate(self, value):
        value = super(EmailField, self).validate(value)

        if not value==None:
            try:
                if value.find('@') == -1:
                    raise self._field_error('invalid email')
            except AttributeError:
                # if no 'find'-method found
                raise self._field_error('invalid email')
            
        return value
        

class PhoneField(Field):

    def validate(self, value):
        value = super(PhoneField, self).validate(value)

        if not value==None and not len(str(value))==11:
            raise self._field_error('invalid phone')

        return value


class DateField(Field):
    
    def validate(self, value):
        value = super(DateField, self).validate(value)

        if not value==None:
            try:
                value = datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                raise self._field_error('invalid date')

        return value


class BirthDayField(DateField):

    def validate(self, value):
        value = super(BirthDayField, self).validate(value)

        if not value==None:
            if datetime.now().year - value.year > 70:
                raise self._field_error('invalid birth date (age must be <= 70)')

        return value


class IntField(Field):

    def validate(self, value):
        value = super(IntField, self).validate(value)

        if not value==None:
            try:
                value = int(value)
            except (ValueError, TypeError):
                raise self._field_error('is not integer')

        return value


class GenderField(IntField):

    def validate(self, value):
        value = super(GenderField, self).validate(value)

        if not value == None:
            if not value in GENDERS.keys():
                raise self._field_error('invalid gender (must be 0, 1 or 2)')

        return value

       
class ClientIDsField(Field):

    def validate(self, value):
        value = super(ClientIDsField, self).validate(value)

        if not value==None:
            if not isinstance(value, list):
                raise self._field_error('not list')
            try:
                value = [int(v) for v in value]
            except (ValueError, TypeError):
                raise self._field_error('values must be integers')

            # for i, v in enumerate(value):
            #         value[i] = int(v)
                
        return value

class ApiRequest(object):
    
    def __init__(self, request_data):
        self.request = request_data
        self.fields = {k:v for k,v in self.__class__.__dict__.iteritems() if issubclass(v.__class__, Field)}

        # check keys -  if all required data passed
        requireds = set(k for k,v in self.fields.iteritems() if v.required)
        remains =  requireds - set(request_data.keys())
        if remains:
            raise ValidationError(message="required", field=requireds.pop())

        # assign and validate fields
        for k,v in request_data.iteritems():
            try:
                self.__setattr__(k, v) # field vailues get validated here
            except FieldValidationError as e:
                raise ValidationError(message=e.message, field=k)

        # run request-wide validation
        self.validate()


    def __str__(self):
        return "<ApiRequest %s fields: >" % (self.__class__.__name__, " ".join(["%s:%s"%(k,v) for k,v in self.fields.iteritems()]))

    def validate(self):
        raise NotImplementedError()

    def process(self, ctx=None, store=None):
        raise NotImplementedError()

class ClientsInterestsRequest(ApiRequest):
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    def validate(self):
        return self

    def process(self, ctx=None, store=None):
        result = {}
        for cid in self.client_ids:
            result[cid] = scoring.get_interests(store, cid)

        ctx.update({'nclients':len(self.client_ids)})
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
            raise ValidationError('None of the pairs (phone, email) or '
                                  '(first_name, last_name) or '
                                  '(birthday, gender) passed')

    def process(self, ctx=None, store=None):
        score = scoring.get_score(None, 
                                  self.phone, 
                                  self.email, 
                                  self.birthday,
                                  self.gender, 
                                  self.first_name, 
                                  self.last_name)

        actual_fields = [f for f in self.fields if not f==None]
        ctx.update({'has':actual_fields})

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

        # check auth 
        logged_id = check_auth(self)
        if not logged_id:
            raise AuthError()

        # handle request
        try:
            self.handler_class = self.__method_handlers__[self.method]
        except KeyError as e:
            raise ValidationError('Method "%s" not found' % self.method)

        return self

    def process(self, ctx, store):
        return self.handler_class(self.arguments).process(ctx, store)


def check_auth(request):
    if request.login == ADMIN_LOGIN:
        digest = hashlib.sha512(datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT).hexdigest()
    else:
        digest = hashlib.sha512(request.account + request.login + SALT).hexdigest()
    if digest == request.token:
        return True
    return False


def method_handler(request, ctx, store):
    try:
        api_request = MethodRequest(request['body'])
        response = api_request.process(ctx, store)
        code = 200
    except ValidationError as e:
        if e.field:
            response = 'field "%s" error: %s' % (e.field, e.message)
        else:
            response = e.message

        code = INVALID_REQUEST

    except AuthError:
        code = FORBIDDEN
        response = 'Forbidden'

    #todo: update ctx - has
    return response, code


class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }

    def get_request_id(self, headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except Exception as e:
            logging.error('request read error: %s', e.message)
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            logging.info("%s: %s %s" % (self.path, data_string, context["request_id"]))
            if path in self.router:
                try:
                    response, code = self.router[path]({"body": request, "headers": self.headers}, context, store)
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

    try:
        store = store.StoreTarantool()
    except Exception as e:
        logging.info('Store init failed, starting with no store. Error: %s', e.message)
        store = None

    server = HTTPServer(("localhost", opts.port), MainHTTPHandler)
    logging.info("Starting server at %s" % opts.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
