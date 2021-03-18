from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from sqlalchemy.orm import Session
from src.connection import db_instance
from src import Models, Schemas
from src.Models import Users, PaymentAccount, PaymentRecord
from src.Schemas import UserIn, User, Record, Account, AccountIn, UserLogin, TokenData, JWTToken, Payment
from typing import List
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import uvicorn


app = FastAPI(title= 'API TEST')

# jwt secret and password hash
secret = 'apitest'
pwd_context = CryptContext(schemes=['bcrypt'], deprecated = 'auto')

# allow cors
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_methods = ["*"],
    allow_headers = ["*"]
)


@app.on_event('startup')
async def startup():
    await db_instance.connect()


@app.on_event('shutdown')
async def shutdown():
    await db_instance.disconnect()


@app.get('/')
def index():
    '''
    Test the api service on Ubuntu server
    '''
    return {'status':'success'}


@app.get('/dbtest')
async def db_test():
    '''
    Test the database service
    '''
    return await db_instance.execute("select datname from pg_database")

@app.get('/users/')
async def get_user():
    '''
    Return all users
    '''
    user_query = Users.select()
    result_list = await db_instance.fetch_all(user_query)
    print(result_list)
    response_list = []
    #list response
    for result in result_list:
        response_list.append({'id':result['id'], 'first':result['first'],'last': result['last'], 'email':result['email']})
    return {'status': 'success', 'result': response_list}


@app.post('/login/')
async def login_user(userInfo: UserLogin):
    '''
    User login via email and password, 
    use default email alanwang0028@gmail.com, password 23456, password hashed
    '''
    user_query = Users.select().where(Users.c.email == userInfo.email)
    query_result = await db_instance.fetch_one(user_query)
    print(userInfo.email, userInfo.password)
    if query_result is None or query_result['email'] is None:
        raise HTTPException(status_code = 404, detail= 'no such user')
    print(query_result['id'])
    if not pwd_context.verify(userInfo.password, query_result['password']):
        raise HTTPException(status_code= 401, detail= 'verification failed')
    else:
        # user verified, generate jwt token
        return {'status': 'success'}



@app.get('/user/{userid}')
async def find_user(userid: int):
    '''
    Find user info by user id, use dafault 1 to test, this is ideally used by management console
    '''
    if userid <= 0 or type(userid) is not int:
        return {'result': 'error'}
    else:
        query = Users.select().where(Users.c.id == userid)
        query_result = await db_instance.fetch_one(query)
        if query_result is None or query_result['id'] is None:
            raise HTTPException(status_code= 404, detail= 'not found')
        else:
            return {
            'status': 'success', 
            'result': 
                {
                'id': query_result['id'],
                'first': query_result['first'],
                'last': query_result['last'],
                'email': query_result['email'],
                }
            }


@app.post('/user/')
async def create_user(user: UserIn):
    '''
    Create a new user, use this api to create a new user, email can not repeat with previous emails
    '''
    check_query = Users.select().where(Users.c.email == user.email)
    check = await db_instance.fetch_one(check_query)
    print(check['email'])
    if type(check) is not None:
        raise HTTPException(status_code= 409, detail= 'already existed')
    else:
        if len(user.password) < 4:
            raise HTTPException(status_code=400, detail='password length should be larger or equal to 4')
        passwd_hash = pwd_context.hash(user.password)
        print(passwd_hash)
        user_query = Users.insert().values(first = user.first, last = user.last, email = user.email, password = passwd_hash)
        new_user = await db_instance.execute(user_query)
        return JSONResponse(status_code=201, content={"result": 'success'})


@app.put('/user/{userid}')
async def edit_user(userid, user: UserIn):
    pass


@app.get('/user/{userid}/accounts/')
async def get_user_account(userid):
    '''
    List user's account info
    '''
    if not isinstance(userid, int):
        raise HTTPException(status_code= 400, detail='bad request')
    query = PaymentAccount.select().where(PaymentAccount.c.user == userid)
    query_result = await db_instance.fetch_all(query)
    return {'status':'success', 'result': query_result}


@app.post('/user/{userid}/account')
async def create_user_account(userid: int,account_info: AccountIn):
    '''
    Create an account, this account is binded to the user, I used an integer simulate bank card number/bank account info
    '''
    if type(userid) is not int:
        raise HTTPException(status_code=400, detail= 'bad request')
    check_query = await db_instance.fetch_one(
        PaymentAccount.select().where(PaymentAccount.c.account_number == account_info.account_number))
    if check_query is not None:
        raise HTTPException(status_code=409, detail= 'account already exists')
    else:
        create_query = PaymentAccount.insert().values(user = userid, account_number = account_info.account_number)
        new_account = await db_instance.execute(create_query)
        return {
            'status':'success',
            'result':new_account
        }



#@app.put('/user/{userid}/account/{account_id}')
async def edit_user_account(userid):
    '''
    Edit the account_number
    '''
    pass


@app.delete('/user/{userid}/account/{account_id}')
async def delete_user_account(userid, account_id):
    '''
    Delete a user account by account id
    '''
    if not userid or not account_id or userid < 1 or account_id:
        raise HTTPException(status_code=400, detail='bad request')
    else:
        delete_query = PaymentAccount.delete().where(PaymentAccount.c.user == userid and PaymentAccount.c.id == account_id)
        delete_result = await db_instance.execute(delete_query)
        return {
            'status':'success',
            'result': delete_result
        }
    


@app.get('/user/{userid}/payrecord')
async def get_user_record(userid: int):
    '''
    Find user's payment list (payout)
    '''
    if userid < 1 or type(userid) != int:
        raise HTTPException(status_code= 400, detail= 'bad request')
    else:
        query = PaymentRecord.select().where(PaymentRecord.c.sender == userid)
        query_result = await db_instance.fetch_all(query)
        return {
            'status':'success',
            'result': query_result
        }

    
payment_memory = []

@app.post('/user/pay/')
async def make_payment(payment: Payment):
    '''
    Simulate the process to make a payout from user A to user B.
    After the post request, a payment record will be generated.
    '''
    if payment.amount <= 0 or payment.sender_account == payment.receiver_account:
        raise HTTPException(status_code=400, detail='bad request')

    # check whether the sender exists
    check_sender = await db_instance.fetch_one(Users.select().where(Users.c.id == payment.sender))
    if check_sender is None:
        print(check_sender['id'])
        raise HTTPException(status_code=404,detail='sender does not exist')

    # check whether the receiver exists
    check_receiver = await db_instance.fetch_one(
        Users.select().where(Users.c.id == payment.receiver)
    )
    if check_receiver is None:
        print(check_receiver)
        raise HTTPException(status_code=404,detail='receiver does not exist')

    # check whether the sender account exists
    check_sender_account = await db_instance.fetch_one(
        PaymentAccount.select().where(PaymentAccount.c.id == payment.sender_account)
    )
    if check_sender_account is None:
        print(check_sender_account)
        raise HTTPException(status_code = 404,detail='sender account does not exist')

    # check whether the receiver account exists
    check_receiver_account = await db_instance.fetch_one(
        PaymentAccount.select().where(PaymentAccount.c.id == payment.receiver_account)
    )
    if check_receiver_account is None:
        print(check_receiver_account)
        raise HTTPException(status_code = 404,detail='receiver account does not exist')
    
    # calculate the transaction fee
    transactionFee = payment.amount * 0.05
    current = datetime.now()
    create_query = PaymentRecord.insert().values(
        sender = payment.sender, 
        receiver = payment.receiver, 
        sender_account = payment.sender_account,
        receiver_account = payment.receiver_account,
        amount = payment.amount,
        transactionFee = transactionFee,
        status = 'Processing',
        create_time = current
    )
    new_record = await db_instance.execute(create_query)
    print(new_record)
    payment_memory.append(new_record)
    return {
        'status': 'success',
        'result': new_record
    }



def send_email(email: str, message = 'payment processed.'):
    mail_host = 'smtp.gmail.com'  

    mail_user = 'Hao Wang'  
    mail_pass = 'xWHA6328116'   

    sender = 'alanwang0028@gmail.com'  
    receiver = email  
    message = MIMEText('content','plain','utf-8')
    message['Subject'] = 'test' 
    message['From'] = sender 
    message['To'] = receiver
    try:
        smtpObj = smtplib.SMTP() 
        smtpObj.connect(mail_host,25)
        print(smtpObj)
        smtpObj.login(mail_user,mail_pass) 
        smtpObj.sendmail(
            sender,receivers,message.as_string()) 
        smtpObj.quit() 
        print('success')
        return {'status': 'success'}
    except smtplib.SMTPException as e:
        print('error',e) #打印错误
        return {'status': e}


if __name__ == '__main__':
    uvicorn.run(app, host = 'localhost')