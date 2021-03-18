from fastapi import HTTPException

class NotFoundException(HTTPException):
    def __init__(self,message = None):
        self.message = message
        super().__init__(status_code= 404, detail=f'{message} not found')

    def __repr__(self):
        return f'status_code = 404, {message} not found'


class BadParamsException(HTTPException):
    def __init__(self, message = None):
        self.message = message
        super().__init__(status_code= 400, detail= f'{message} bad request')

    def __repr__(self):
        return f'status_code = 400, {message} bad request'
