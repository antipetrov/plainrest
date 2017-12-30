#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

import api


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

    def test_method_request_validation(self):
        request_data = {"account": "test_partner", 
                        "login": "test_login", 
                        "method": "online_score", 
                        "token":'123123', 
                        "arguments": None}

        api_request = api.MethodRequest(request_data)

    def test_method_online_score(self):
        request_data = {"account": "test_partner", 
                        "login": "test_login", 
                        "method": "online_score", 
                        "token":'123123', 
                        "arguments": {
                            'phone':'79001112233', 
                            'email':'test@test.test', 
                            'fist_name':'firstname', 
                            'last_name':'lastname',
                            'birthday':'01.01.1988',
                            'gender':'0',
                            }}

        response, code = api.method_handler(request_data, {}, None)

        self.assertIsInstance(response, dict)
        self.assertTrue(response.has_key('score'))

    def test_method_online_score_error(self):
        request_data = {"account": "test_partner", 
                        "login": "test_login", 
                        "method": "online_score", 
                        "token":'123123', 
                        "arguments": {
                            # 'phone':'79001112233', 
                            # 'email':'test@test.test', 
                            'fist_name':'firstname', 
                            'last_name':'lastname',
                            'birthday':'01.01.1988',
                            'gender':'0',
                            }}

        response, code = api.method_handler(request_data, {}, None)
        print(response, code)

        
        self.assertEqual(code, 422)
        self.assertIsInstance(response, dict)
        self.assertTrue(result.has_key('error'))
        self.assertTrue(result['error'].find('phone') > -1)


    def test_method_client_interests(self):
        request_data = {"account": "test_partner", 
                        "login": "test_login", 
                        "method": "client_instrests", 
                        "token":'123123', 
                        "arguments": {
                            "client_ids":['1','2'],
                            "date":"01.02.2008"
                            }}

        response, code = api.method_handler(request_data, {}, None)
        
        self.assertEqual(code, 200)
        self.assertIsInstance(response, dict)
        self.assertTrue(result.has_key('1'))
        self.assertTrue(result.has_key('2'))

    def test_method_client_interests_error(self):
        request_data = {"account": "test_partner", 
                        "login": "test_login", 
                        "method": "client_instrests", 
                        "token":'123123', 
                        "arguments": {
                            "client_ids":['1','2'],
                            "date":"-----"
                            }}

        response, code = api.method_handler(request_data, {}, None)
        
        self.assertEqual(code, 422)
        self.assertIsInstance(response, dict)
        self.assertTrue(result.has_key('error'))
        self.assertTrue(result['error'].find('date') > -1) # в ошибке упоминается имя пофейленного поля

        

if __name__ == "__main__":
    unittest.main()
