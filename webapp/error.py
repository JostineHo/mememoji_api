from app import app
from flask import jsonify


class Error(Exception):
    '''
    To return an error to the client, simply 'raise' an instance of this class at
    any point while you are processing the request. Flask is configured to 'catch'
    the raised exception and turn it into a proper error response to the client.
    '''

    def __init__(self, code, message, http_status=400):
        self.code = code
        self.message = message
        self.http_status = http_status

    def response(self):
        error_dict = {'code': self.code, 'message': self.message}
        response = jsonify(error_dict)
        response.status_code = self.http_status
        return response


@app.errorhandler(Error)
def error_raised(error):
    return error.response()


@app.errorhandler(404)
def not_found(_):
    return Error(404, 'Resource not found', 404).response()
