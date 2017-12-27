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
        print(api_request)

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

        api_request = api.MethodRequest(request_data)
        print(api_request)


if __name__ == "__main__":
    unittest.main()
