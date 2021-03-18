from pydantic import BaseModel
from datetime import date


class UserIn(BaseModel):
    '''
    UserIn schema, create user request, http request body
    '''
    first: str
    last: str
    email: str
    password: str
    
    class Config:
        orm_mode = True


class UserLogin(BaseModel):
    '''
    UserLogin schema, user login post request, http request body
    '''
    email: str
    password: str

    class Config:
        orm_mode = True
    

class User(BaseModel):
    '''
    User model, represent the http response
    '''
    id: int
    first: str
    last: str
    email: str

    class Config:
        orm_mode = True


class AccountIn(BaseModel):
    account_number: int

    class Config:
        orm_mode = True


class Account(BaseModel):
    user: int
    account_number: int

    class Config:
        orm_mode = True


class Payment(BaseModel):
    sender: int
    receiver: int
    sender_account: int
    receiver_account: int
    amount: float

    class Config:
        orm_mode = True


class Record(BaseModel):
    id: int
    sender: int
    receiver: int
    sender_account: int
    receiver_account: int
    amount: float
    transactionFee: float
    status: str
    create_time: date

    class Config:
        orm_mode = True


class JWTToken(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    #email: Optional[str] = None
    pass