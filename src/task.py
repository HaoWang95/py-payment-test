import celery
import threading
from time import sleep
import asyncio
from .Models import PaymentRecord, PaymentAccount, PaymentRecordModel,AccountModel
from .connection import db_instance, DATABASE_URL
from fastapi import BackgroundTasks
from celery.utils.log import get_task_logger
#import sys
#sys.path.append('..')
#from main import get_db


def init_workder(**kwargs):
    pass


celery_instance = celery.Celery('task', broker='amqp://guest:guest@127.0.0.1:5672//')



@celery_instance.task(bind = True)
def test(self, msg):
    '''
    Define background, will be executed after 5 seconds
    '''
    sleep(5)
    return msg[::-1]


@celery_instance.task(bind = True, serializer='json')
async def updateStatus(self, payment_id, status):
    sleep(10)
    logger.info(f'starts to execute updateStatus task for payment_id = {payment_id} ')
    #Before setting the status, check the record
    #search_record = await check_record(payment_id)
    record = await db_instance.fetch_one(
        PaymentRecord.select().where(PaymentRecord.c.id==payment_id)
    )
    if record:
        amount_transferred = record['amount'] + record['transactionFee']
        sender_acc = record['sender_account']
        print('updateStatus', sender_acc)
        sender_account = await db_instance.fetch_one(
            PaymentAccount.select().where(PaymentAccount.c.id == sender_acc)
        )
        sender_account_deposit = sender_account['deposit']
        print('deposit',sender_account_deposit)
        if amount_transferred > sender_account_deposit:
            # amount of money being transferred is larger than the actual deposit value,
            # set this payment to cancelled or deleted, a proper status value
            await db_instance.execute(PaymentRecord.update().where(PaymentRecord.c.id == payment_id).values(is_deleted = 'Cancelled'))
        else:
            # the amount being transferred is legal,
            update_query = PaymentRecord.update().where(PaymentRecord.c.id == payment_id).values(is_deleted = 'Cleared')
            await db_instance.execute(update_query)
    return 'done'



@celery_instance.task(bind = True)
def updateStat_sync(self, payment_id, status):
    sleep(10)
    #PaymentRecord.query()
    return 'done'



async def check_record(payment_id) -> bool :
    '''
    Check whether the amount of money transferred is smaller than the amount of money in the account -> return True
    If the amount of money transferred is higher than the amount of money in the account -> return False
    '''
    check_query = PaymentRecord.select().where(PaymentRecord.c.id == payment_id)
    current_record = await db_instance.fetch_one(check_query)
    #print(current_record)
    #The current_record is a coroutine obj
    if current_record:
        print('check_record', (current_record))
        print('check_record', current_record['sender_account'])
        #current_account = await db_instance.fetch_one(current_record['sender_account'])
        return True
    else:
        return False
