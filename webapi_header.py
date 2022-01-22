#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import psycopg2
from flask_restful import reqparse

def connect_to_db():
    con = psycopg2.connect(
        host = "localhost",
        database = "test_db",
        user = "postgres",
        password = "password",
        port = "5432"        
    )
    return con,con.cursor()

def set_args(*args):
    parser = reqparse.RequestParser()
    
    # check which arguments are present
    if 'orderId' in args:
        parser.add_argument('orderId', required=True, type=int)
        
    if 'clientId' in args:
        parser.add_argument('clientId', required=True, type=int)
    
    if 'productId' in args:
        parser.add_argument('productId', required=True, type=int)
    
    if 'productlist' in args:
        parser.add_argument('productId', required=True, type=int, 
                            action='append')
    
    if 'status' in args:
        parser.add_argument('status', required=False, default = 'Released',
                            type=str)
    
    if 'addflag' in args:
        parser.add_argument('addflag', required=False, default = 0, type=int)
    
    if 'unitPrice' in args:
        parser.add_argument('unitPrice', required=True, type=float)
    
    return parser.parse_args()

def if_cancelled(cursor,orderid):
    check_query = 'SELECT status FROM orders WHERE order_id = ' +\
                str(orderid)
    try:
        cursor.execute(check_query)
    except:
        return 1
        
    checkflag = cursor.fetchone()
    if checkflag is None:
        return 2
    if checkflag[0] == 'Cancelled':
        return 3
    
    return 0
    
    