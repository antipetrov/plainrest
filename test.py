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

    def test_method_request_unvalidate(self):
        request_data = {"account": "test_partner", 
                        "login": "test_login", 
                        "method": "online_score", 
                        "token":'123123', 
                        "arguments": None}

        api_request = api.MethodRequest(request_data)
        print(api_request)


if __name__ == "__main__":
    unittest.main()
