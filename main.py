from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from sqlalchemy.orm import Session
from src.connection import db_instance, LocalSession
from src import Models, Schemas
from src.Models import Users, PaymentAccount, PaymentRecord
from src.Schemas import UserIn, UserUpdate, User, Record, Account, AccountIn, UserLogin, TokenData, JWTToken, Payment, AccountUpdate
from typing import List
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi.responses import JSONResponse
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from random import uniform
from src.task import celery_instance, test, updateStatus, updateStat_sync
import src.UserController as UserController
from src.connection import DATABASE_URL
import uvicorn


app = FastAPI(
    title= 'API TEST',
    description = 'task queue testing is ongoing',
    version = '1.0'
)

# jwt secret and password hash
secret = 'apitest'
pwd_context = CryptContext(schemes=['bcrypt'], deprecated = 'auto')

@app.middleware("http")
async def db_session_middleware(request: Request, call_next):
    response = Response('Init response, server internal err', status_code = 500)
    try:
        request.state.db = LocalSession()
        response = await call_next(request)
    finally:
        request.state.db.close()
    return response

# allow cors
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins = origins,
    allow_methods = ["*"],
    allow_headers = ["*"]
)


# Build the dependency
def get_db(http_req: Request):
    return http_req.state.db


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
    Test the postgresql database service
    '''
    return await db_instance.execute("select datname from pg_database")



@app.get('/users/')
async def get_user():
    '''
    Return all users, using async approach
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
    use default email alanwang0028@gmail.com, password 23456 (in str format), password hashed,
    TODO: add jwt, use token as dependency
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
    Find user info by user id, use dafault 1 to test, this is ideally used by management console,
    default testing value, 1 or 2
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


@app.get('/user/v2/{userid}')
def find_user_v2(userid: int, db:Session = Depends(get_db)):
    '''
    Using sync approach to retrive user data, returned result contains hashed password,
    default testint value 1 or 2
    '''
    print(userid)
    user_info = UserController.get_user(db, userid)
    if user_info is None:
        raise HTTPException(status_code = 404, detail = 'user not found')
    print(user_info)
    return {
        'status':'success',
        'result':user_info
    }


@app.get('/users/v2/')
def find_users_v2(db:Session = Depends(get_db)):
    '''
    Using sync approach to get the list of users, returned results contain hashed password
    No pagination
    '''
    users = UserController.get_users(db)
    if users is None:
        raise HTTPException(status_code = 404, detail = 'db is empty')
    return {
        'status':'testing',
        'results':users
    }


@app.post('/user/')
async def create_user(user: UserIn):
    '''
    Create a new user, use this api to create a new user, email can not repeat with previous emails
    TODO: password strength + email binding, notification
    '''
    check_query = Users.select().where(Users.c.email == user.email)
    check = await db_instance.fetch_one(check_query)
    if check is not None:
        raise HTTPException(status_code= 409, detail= 'already existed')
    else:
        if len(user.password) < 4:
            raise HTTPException(status_code=400, detail='password length should be larger or equal to 4')
        passwd_hash = pwd_context.hash(user.password)
        print(passwd_hash)
        user_query = Users.insert().values(first = user.first, last = user.last, email = user.email, password = passwd_hash)
        new_user = await db_instance.execute(user_query)
        return JSONResponse(status_code=201, content={"result": 'success'})


@app.patch('/user/{userid}')
async def edit_user(userid: int, user: UserUpdate):
    '''
    This is a partial update, leaving the rest intact
    Password reset can not be achieved via this api.
    first -> first name
    last -> last name
    email -> email
    '''

    if userid is None:
        raise HTTPException(status_code = 400, detail = 'bad request params')
    check = await db_instance.fetch_one(
        Users.select().where(Users.c.id == userid)
    )
    if check is None:
        raise HTTPException(status_code = 404, detail = 'user does not exist')
    else:
        print(check)
        if user.first == "string" or user.last == "string" or user.email == "string":
            raise HTTPException(status_code = 400, detail = 'do not use value string as testing data')

        updated = await db_instance.execute(
            Users.update().where(Users.c.id == userid).values(**user.dict())
        )
        return {
            'status':'testing done',
            'results': updated
        }


@app.get('/user/{userid}/accounts/')
async def get_user_account(userid:int):
    '''
    List user's account info
    '''
    try:
        print(type(userid), userid)
        query = PaymentAccount.select().where(PaymentAccount.c.user == userid)
        query_result = await db_instance.fetch_all(query)
        return {'status':'success', 'result': query_result}
    except err as e:
        return e


@app.post('/user/{userid}/account')
async def create_user_account(userid: int,account_info: AccountIn):
    '''
    Create an account, this account is binded to the user, I used an integer
    to simulate bank card number/bank account info, and randomly generate a deposit
    value to represent the amount of money
    '''
    if type(userid) is not int:
        raise HTTPException(status_code=400, detail= 'bad request')
    check_query = await db_instance.fetch_one(
        PaymentAccount.select().where(PaymentAccount.c.account_number == account_info.account_number))
    if check_query is not None:
        raise HTTPException(status_code=409, detail= 'account already exists')
    else:
        # save to 2 digits
        deposit = round(uniform(500.0, 10000.0), 2)
        create_query = PaymentAccount.insert().values(user = userid, account_number = account_info.account_number, deposit = deposit)
        new_account = await db_instance.execute(create_query)
        return {
            'status':'success',
            'result':new_account
        }

@app.patch('/user/{userid}/account/{account_id}')
async def edit_user_account(userid: int, account_id:int, account_info: AccountUpdate):
    '''
    Simulate the process that a user edits the account, since the account_number attribute
    is faked as a number, user can only change the deposit value for the account
    '''
    print(account_info)
    if userid is None or account_id is None:
        raise HTTPException(status_code = 400, detail='bad request')
    if account_info.deposit < 0 or account_info.deposit > 100000:
        raise HTTPException(status_code = 400, detail = 'bad request')
    await db_instance.execute(
        PaymentAccount.update().where(PaymentAccount.c.id == account_id).values(
            deposit = account_info.deposit
        )
    )
    result = await db_instance.fetch_one(
        PaymentAccount.select().where(PaymentAccount.c.id == account_id)
    )
    return{
        'status':'success',
        'result': result
    }



@app.delete('/user/{userid}/account/{account_id}')
async def delete_user_account(userid: int, account_id: int):
    '''
    Delete a user account by account id,
    (set the account attribute to true to represent deleted then the account info can still be accessed via management console)
    '''
    if not userid or not account_id or int(userid) < 1 or int(account_id) < 1:
        raise HTTPException(status_code=400, detail='bad request')
    else:
        # set payment_accounts record to deleted rather than delete the record
        delete_query = PaymentAccount.update().where(
            (PaymentAccount.c.user == int(userid))&(PaymentAccount.c.id == int(account_id))).values(account_status = True)
        return {
            'status':'success',
            'result': await db_instance.execute(delete_query)
        }


@app.get('/user/{userid}/payrecord')
async def get_user_record(userid: int):
    '''
    Find user's payment list (payout), for testing, use 1,
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
    transactionFee = amount * 0.05
    '''
    if payment.amount <= 0 or payment.sender_account == payment.receiver_account:
        raise HTTPException(status_code=400, detail='bad request')

    # check whether the sender exists
    check_sender = await db_instance.fetch_one(Users.select().where(Users.c.id == payment.sender))
    if check_sender is None:
        #print(check_sender['id'])
        raise HTTPException(status_code=404,detail='sender does not exist')

    # check whether the receiver exists
    check_receiver = await db_instance.fetch_one(
        Users.select().where(Users.c.id == payment.receiver)
    )
    if check_receiver is None:
        #print(check_receiver)
        raise HTTPException(status_code=404,detail='receiver does not exist')

    # check whether the sender account exists
    check_sender_account = await db_instance.fetch_one(
        PaymentAccount.select().where(PaymentAccount.c.id == payment.sender_account)
    )
    if check_sender_account is None:
        #print(check_sender_account)
        raise HTTPException(status_code = 404,detail='sender account does not exist')

    # check whether the receiver account exists
    check_receiver_account = await db_instance.fetch_one(
        PaymentAccount.select().where(PaymentAccount.c.id == payment.receiver_account)
    )
    if check_receiver_account is None:
        #print(check_receiver_account)
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
        is_deleted = 'Processing',
        create_time = current
    )
    new_record = await db_instance.execute(create_query)
    print(new_record)
    # reduce the corresponding amount of money
    PaymentAccount.update().where(PaymentAccount.c.user == payment.sender_account).values(deposit = PaymentAccount.c.deposit - transactionFee - payment.amount)
    return {
        'status': 'success',
        'result': new_record
    }



def send_email(email: str, message = 'payment processed.'):
    mail_host = 'smtp.gmail.com'

    mail_user = ''
    mail_pass =''

    sender = ''
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
        print('error',e)
        return {'status': e}


@app.post('/testCelery')
async def testCelery(msg = 'test'):
    '''
    Test the celery task queue, celery+rabbitmq to handle background tasks
    '''
    test.apply_async(args=[msg], link = test.s())
    return {'status': 'celery is working at background'}


@app.post('/testQueue')
def testQueue():
    '''
    Update the task into celery queue, test whether celery queue is online
    '''
    #import asyncio
    #loop = asyncio.get_event_loop()
    #loop.run_until_complete(updateStatus.apply_async([1,'Cleared']))
    #asyncio.get_event_loop().run_until_complete(updateStatus.apply_async([1,'Cleared']))
    #payment_id = 1
    #status = 'test'

    updateStat_sync.apply_async(args = [1,'Cleared'])
    return {
            'status': 'celery async test done.'
        }

@app.post('/reset')
def processPayment():
    '''
    For all payment records, reset to processing
    '''
    return {
        'status':'success'
    }
