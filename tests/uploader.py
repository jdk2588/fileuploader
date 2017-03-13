import json

from utils import tokengen
from base import BaseTestCase

class FileUploaderHandlerTest(BaseTestCase):

    '''Test to upload a file, a PDF file of size 242KB'''
    def test_A_upload_file(self):
        data = open('files/sample.pdf', 'rb').read()
        self.headers["Content-Type"] = "application/pdf"
        self.post('upload', data)
        self.assertFalse(self.response.error)
        body = json.loads(self.response.body.decode("utf-8"))

        self.assertIn('code', body)
        self.assertEqual(200, body['code'])

        for e in ["token"]:
            self.assertIn(e, body['data'])
            if e == "token":
                BaseTestCase.token = body['data']['token']


    '''Test to return message in case file is still uploaded'''
    def test_B_status_still_uploaded(self):
        self.get('token/%s' % self.token)
        self.assertFalse(self.response.error)
        body = json.loads(self.response.body.decode("utf-8"))

        self.assertIn('code', body)
        self.assertEqual(200, body['code'])

        self.assertEqual("The file is still being uploaded", body['message'])
        for e in ["is_uploaded"]:
            self.assertIn(e, body['data'])

            if e == "is_uploaded":
                self.assertEqual(False, body['data'][e])

    '''Test to check for an invalid token'''
    def test_C_status_invalid_file(self):
        self.sleep = True
        token = tokengen()
        self.get('token/%s' % token)
        body = json.loads(self.response.body.decode("utf-8"))

        self.assertIn('code', body)
        self.assertEqual(404, body['code'])
        self.assertIn("reason", body['error'])

        self.assertEqual("InvalidFile", body['error']['reason'])

    '''Redirect params of the uploaded file'''
    def test_D_get_redirect_url(self):
        self.sleep = True
        self.sleep_time = 65
        self.get('token/%s' % self.token, follow_redirects=False)

        self.assertIn("Location", self.response.headers)
        BaseTestCase.signed_url = self.response.headers.get("Location")
        self.assertEqual(302, self.response.code)
        self.assertIn("Content-Type", self.response.headers)
        self.assertEqual("application/pdf", self.response.headers.get("Content-Type"))
        BaseTestCase.signed_url = self.response.headers.get("Location")


    '''Make a call after one minute, should expire'''
    def test_E_check_expired_urll(self):
        #self.sleep = True
        #self.sleep_time = 60
        self.external_request(BaseTestCase.signed_url)
        self.assertEqual(403, self.response.code)
