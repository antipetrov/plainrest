#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import unittest
import api
import store

cases = {api.CharField:{'success':[1,None, ]}}

class TestFields(unittest.TestCase):

    def setUp(self):
        class FieldContainer(object):
            char_field = api.CharField(nullable=False)
            int_field = api.IntField(nullable=False)
            arg_field = api.ArgumentsField(nullable=False)
            email_field = api.EmailField(nullable=False)
            phone_field = api.PhoneField(nullable=False)
            date_field = api.DateField(nullable=False)
            birthday_field = api.BirthDayField(nullable=False)
            gender_field = api.GenderField(nullable=False)
            ids_field = api.ClientIDsField(nullable=False)

        self.contaier = FieldContainer()

    def test_nullable(self):
        with self.assertRaises(api.FieldValidationError):
            self.contaier.char_field = None

    def test_char_field(self):
        self.contaier.char_field = 'str'
        self.assertEqual(self.contaier.char_field, 'str')

        self.contaier.char_field = 1
        self.assertEqual(self.contaier.char_field, 1)

    def test_int_field(self):
        self.contaier.int_field = 1
        self.assertEqual(self.contaier.int_field, 1)

    def test_int_field_fail(self):
        with self.assertRaises(api.FieldValidationError):
            self.contaier.int_field = 'str'

    def test_argument_field(self):        
        value = {'1':'1'}
        self.contaier.arg_field = value
        self.assertEqual(self.contaier.arg_field, value)

        value = {}
        self.contaier.arg_field = value
        self.assertEqual(self.contaier.arg_field, value)


        with self.assertRaises(api.FieldValidationError):
            self.contaier.arg_field = 'str'
        
        with self.assertRaises(api.FieldValidationError):
            self.contaier.arg_field = 1

    def test_email_field(self):        
        value = 'test@email.com'
        self.contaier.email_field = value
        self.assertEqual(self.contaier.email_field, value)

        with self.assertRaises(api.FieldValidationError):
            self.contaier.email_field = 'test'
        
        with self.assertRaises(api.FieldValidationError):
            self.contaier.email_field = 1

    def test_phone_field(self):
        value = '12345678901'
        self.contaier.phone_field = value
        self.assertEqual(self.contaier.phone_field, value)
        value = 12345678901
        self.contaier.phone_field = value
        self.assertEqual(self.contaier.phone_field, value)

        with self.assertRaises(api.FieldValidationError):
            self.contaier.phone_field = '0000'
        
        with self.assertRaises(api.FieldValidationError):
            self.contaier.phone_field = 1234567890123

    def test_date_field(self):
        self.contaier.date_field = '01.01.2017'
        self.assertEqual(self.contaier.date_field, datetime.datetime.strptime('01.01.2017', '%d.%m.%Y'))

        with self.assertRaises(api.FieldValidationError):
            self.contaier.date_field = 'test'
        
        with self.assertRaises(api.FieldValidationError):
            self.contaier.date_field = '2019.01.01'

    def test_birthday_field(self):
        self.contaier.date_field = '01.01.2017'
        self.assertEqual(self.contaier.date_field, datetime.datetime.strptime('01.01.2017', '%d.%m.%Y'))
        
        with self.assertRaises(api.FieldValidationError):
            self.contaier.date_field = '1900.01.01'

        with self.assertRaises(api.FieldValidationError):
            self.contaier.date_field = '2100.01.01'

    def test_gender_field(self):
        self.contaier.gender_field = 1
        self.assertEqual(self.contaier.gender_field, 1)

        self.contaier.gender_field = '0'
        self.assertEqual(self.contaier.gender_field, 0)
        
        with self.assertRaises(api.FieldValidationError):
            self.contaier.gender_field = {}

        with self.assertRaises(api.FieldValidationError):
            self.contaier.gender_field = 4

    def test_ids_field(self):
        self.contaier.ids_field = [1,2,3]
        self.assertEqual(self.contaier.ids_field, [1,2,3])
        self.contaier.ids_field = ['1','2','3']
        self.assertEqual(self.contaier.ids_field, [1,2,3])
        
        with self.assertRaises(api.FieldValidationError):
            self.contaier.ids_field = 1

        with self.assertRaises(api.FieldValidationError):
            self.contaier.ids_field = ['a','e']

        with self.assertRaises(api.FieldValidationError):
            self.contaier.ids_field = ['1',None]


def test_data_provider(data):
    def test_decorator(func):
        def test_wrapper(self):
            # print(data)
            for d in data:
                try:
                    print(d)
                    func(self, d)
                except AssertionError as e:
                    raise AssertionError('%s. (data:%s)', e.message, repr(d))
            
        return test_wrapper 
    return test_decorator


class TestRequest(unittest.TestCase):

    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = None

    @test_data_provider([{"method":"online_score", "arguments": {'phone':'79001112233', 'email':'test@test.test', 'first_name':'firstname', 'last_name':'lastname', 'birthday':'01.01.1988', 'gender':'0'}, "account": "111", "login": "test", "token":'6909573a28d6b12900257df0064967141fb2cd5e82b6c269f3aaf49a0b450749e75872e4a717b90687e7f65bac6c59c0865ecafc467da803a634d5d0079ee9f5'}])
    def test_score(self, request_data):
        response, code = api.method_handler({'body':request_data, 'headers':self.headers}, {}, None)


class TestSuite(unittest.TestCase):
    def setUp(self):
        self.context = {}
        self.headers = {}
        self.store = None

    def get_response(self, request):
        return api.method_handler({"body": request, "headers": self.headers}, self.context, self.store)

    def test_empty_request(self):
        _, code = self.get_response({})
        self.assertEqual(api.INVALID_REQUEST, code)

    def test_auth_error(self, ):
        request_data = {"account": "111", 
                        "login": "test", 
                        "token":'0', 
                        "method": "client_instrests", 
                        "arguments": {
                            "client_ids":['1','2'],
                            "date":"-----"
                            }}

        response, code = api.method_handler(request_data, {}, None)

        self.assertTrue(code, 403)
        self.assertEqual(response, 'Forbidden')

    @test_data_provider([{"method":"online_score", "arguments": {'phone':'79001112233', 'email':'test@test.test', 'first_name':'firstname', 'last_name':'lastname', 'birthday':'01.01.1988', 'gender':'0'}, "account": "111", "login": "test", "token":'6909573a28d6b12900257df0064967141fb2cd5e82b6c269f3aaf49a0b450749e75872e4a717b90687e7f65bac6c59c0865ecafc467da803a634d5d0079ee9f5'},
                         {"method":"online_score", "arguments": {'email':'test@test.test', 'first_name':'firstname', 'last_name':'lastname', 'birthday':'01.01.1988', 'gender':'0'}, "account": "111", "login": "test", "token":'6909573a28d6b12900257df0064967141fb2cd5e82b6c269f3aaf49a0b450749e75872e4a717b90687e7f65bac6c59c0865ecafc467da803a634d5d0079ee9f5'},
                         {"method":"online_score", "arguments": {'email':'test@test.test', 'last_name':'lastname'}, "account": "111", "login": "test", "token":'6909573a28d6b12900257df0064967141fb2cd5e82b6c269f3aaf49a0b450749e75872e4a717b90687e7f65bac6c59c0865ecafc467da803a634d5d0079ee9f5'},
        ])
    def test_online_score(self, request_data):
        response, code = self.get_response(request_data)
        self.assertIsInstance(response, dict)
        self.assertTrue(response.has_key('score'))

    def test_method_online_score_error(self):
        request_data = {"account": "111", 
                        "login": "test", 
                        "token":'6909573a28d6b12900257df0064967141fb2cd5e82b6c269f3aaf49a0b450749e75872e4a717b90687e7f65bac6c59c0865ecafc467da803a634d5d0079ee9f5', 
                        "method":"online_score",
                        "arguments": {}}

        response, code = api.method_handler(request_data, {}, None)

        self.assertEqual(code, 422)
        self.assertTrue(response.find('phone') > -1)


    def test_method_client_interests(self):
        request_data = {"account": "111", 
                        "login": "test", 
                        "token":'6909573a28d6b12900257df0064967141fb2cd5e82b6c269f3aaf49a0b450749e75872e4a717b90687e7f65bac6c59c0865ecafc467da803a634d5d0079ee9f5', 
                        "method":"client_instrests",
                        "arguments": {
                            "client_ids":['1','2'],
                            "date":"01.02.2008"
                            }}

        response, code = api.method_handler(request_data, {}, None)
        
        self.assertEqual(code, 200)
        self.assertIsInstance(response, dict)
        self.assertTrue(response.has_key(1))
        self.assertTrue(response.has_key(2))

    def test_method_client_interests_error(self):
        request_data = {"account": "111", 
                        "login": "test", 
                        "token":'6909573a28d6b12900257df0064967141fb2cd5e82b6c269f3aaf49a0b450749e75872e4a717b90687e7f65bac6c59c0865ecafc467da803a634d5d0079ee9f5', 
                        "method":"client_instrests",
                        "arguments": {
                            "client_ids":['1','2'],
                            "date":"-----"
                            }}

        response, code = api.method_handler(request_data, {}, None)
        
        self.assertEqual(code, 422)
        self.assertTrue(response.find('date') > -1) # в ошибке упоминается имя пофейленного поля

    def test_context_score(self):
        request_data = {"account": "111", 
                        "login": "test", 
                        "token":'6909573a28d6b12900257df0064967141fb2cd5e82b6c269f3aaf49a0b450749e75872e4a717b90687e7f65bac6c59c0865ecafc467da803a634d5d0079ee9f5', 
                        "method":"online_score",
                        "arguments": {
                            'phone':'79001112233', 
                            'email':'test@test.test', 
                            'first_name':'firstname', 
                            'last_name':'lastname',
                            'birthday':'01.01.1988',
                            'gender':'0',
                            }}

        response, code = api.method_handler(request_data, self.context, None)
        
        self.assertEqual(self.context.has_key('has'), True)
        self.assertEqual(self.context['has'], request_data['arguments'].keys())

    def test_context_interests(self):
        request_data = {"account": "111", 
                "login": "test", 
                "token":'6909573a28d6b12900257df0064967141fb2cd5e82b6c269f3aaf49a0b450749e75872e4a717b90687e7f65bac6c59c0865ecafc467da803a634d5d0079ee9f5', 
                "method":"client_instrests",
                "arguments": {
                    "client_ids":['1','2'],
                    "date":"01.02.2008"
                    }}

        response, code = api.method_handler(request_data, self.context, None)
        
        self.assertEqual(self.context.has_key('nclients'), True)
        self.assertEqual(self.context['nclients'], 2)

    # def test_full_request(self):
    #     request_data = {"account": "111", 
    #                     "login": "test", 
    #                     "token":'6909573a28d6b12900257df0064967141fb2cd5e82b6c269f3aaf49a0b450749e75872e4a717b90687e7f65bac6c59c0865ecafc467da803a634d5d0079ee9f5', 
    #                     "method":"online_score",
    #                     "arguments": {
    #                         'phone':'79001112233', 
    #                         'email':'test@test.test', 
    #                         'first_name':'firstname', 
    #                         'last_name':'lastname',
    #                         'birthday':'01.01.1988',
    #                         'gender':'0',
    #                         }}        



class TestStore(unittest.TestCase):
    def setUp(self):
        self.db = store.StoreTarantool()

    def test_store_write_read(self):
        test_value = 'test_val'
        self.db.set('test1', test_value)

        value = self.db.get('test1')
        self.assertEqual(value, test_value)

    def test_store_cache_write_read(self):
        test_value = 'test_val'
        self.db.cache_set('test1', test_value)

        value = self.db.cache_get('test1')
        self.assertEqual(value, test_value)


    def test_store_connection(self):
        db = store.StoreTarantool(host='---')
        self.assertEqual(db.connection, None)



        

if __name__ == "__main__":
    unittest.main()
