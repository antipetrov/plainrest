#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import api

class TestFields(unittest.TestCase):

    def setUp(self):
        pass

    def test_charfield(self):
        class FieldContainer(object):
            char_field = api.CharField(nullable=False)

        contaier = FieldContainer()
        contaier.char_field = 'str'
        self.assertEqual(contaier.char_field, 'str')

        contaier.char_field = 1
        self.assertEqual(contaier.char_field, 1)
        
        with self.assertRaises(api.FieldValidationError):
            contaier.char_field = None
            print(field)




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

    def test_auth_error(self):
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


    def test_method_online_score(self):
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

        response, code = api.method_handler(request_data, {}, None)
        

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






        

if __name__ == "__main__":
    unittest.main()
