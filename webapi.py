#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jan 22 07:38:11 2022

@author: rodrigocampos
"""

import flask
from flask_restful import Resource, Api
import webapi_header

app = flask.Flask(__name__)
clubbi_api = Api(app)

if __name__ == "__main__":
    app.run(debug=True)
    

class orders(Resource):
    # get all items and total price of an order
    @app.route('/orders',methods=['GET'])
    def get(self):
        # connect to database
        con, cur = webapi_header.connect_to_db()
        
        # parse input
        args = webapi_header.set_args('orderId')
 
        # arguments
        order_id = args['orderId']
        
        # get items
        item_query = 'SELECT product_id, description FROM items ' +\
                'WHERE order_id = ' + str(order_id)
        
        try:
            cur.execute(item_query)
        except:
            return {'Bad gateway' : None}, 502
            
        products = cur.fetchall()
        products_ids = []
        products_desc = []
        
        # get price
        prod_str = ''
        for product in products:
             prod_str += '{product[0]}, '
             products_ids.append(product[0])
             products_desc.append(product[1])
        prod_str = prod_str[:-1]
        
        prod_desc_str = ''
        for product in products:
             prod_desc_str += '{product[1]}, '
        prod_desc_str
        
        # check whether order was cancelled first
        status_code = webapi_header.if_cancelled(cur,order_id)
        if status_code == 1:
            return {'Bad gateway' : None}, 502
        elif status_code == 2:
            return {'Invalid order ID' : None}, 404
        elif status_code == 3:
            return {'This order was cancelled.' : None}, 404
        
        # output items and total price of order
        price_query = 'SELECT SUM(unit_price) FROM items ' +\
                    'WHERE order_id = ' + str(order_id) 
        try:
            cur.execute(price_query)
        except:
            return {'Bad gateway' : None}, 502
        
        total_price = cur.fetchone()[0]
        
        con.close()
        
        if total_price is not None:
            return {'Products ordered by ID:' : products_ids,
                    'Products ordered by description:' : products_desc,    
                    'Total price of order:' : '{:.2f}'.format(total_price)},200
        else:
            return {'This order is invalid' : None}, 404
            
        
    # add new order
    @app.route('/orders',methods=['POST'])
    def post(self):
        # connect to database
        con, cur = webapi_header.connect_to_db()
        
        # parse input
        args = webapi_header.set_args('clientId','productlist','status')
 
        # arguments
        client_id = args['clientId']
        product_list = args['productId']
        status = args['status']
        
        # update orders table
        order_query = 'INSERT INTO orders(client_id, status)' +\
                    'VALUES (' + str(client_id) + ',\'' + status + '\') ' +\
                    'RETURNING order_id'       
        try:
            cur.execute(order_query)
        except:
            return {'Bad gateway' : None}, 502
        
        last_order_id = cur.fetchone()[0]

        con.commit()
        
        # update items table (only order_id of item is changed)
        product_str = ''
        for product in product_list:
            product_str += str(product) + ','
        product_str = product_str[:-1]
        
        item_query = 'UPDATE items SET order_id = ' + str(last_order_id) +\
                    ' WHERE product_id IN (' + product_str + ') AND ' +\
                    ' order_id IS NULL RETURNING product_id'                  
        try:
            cur.execute(item_query)
        except:
            return {'Bad gateway' : None}, 502
        
        accepted_orders = cur.fetchall()

        con.commit()

        con.close()
        
        if len(accepted_orders) == len(product_list):
            return {'Order accepted' : None},200
        else:
            return {'Some items are not available or' +\
                    ' were duplicated during order.' +\
                    ' Only the following items were accepted' : 
                        accepted_orders}, 404
 
    # update products in order
    # addflag = True: product is added to order
    # addflag = False: product is removed from order
    @app.route('/orders',methods=['PUT'])
    def put(self):
        # connect to database
        con, cur = webapi_header.connect_to_db()
        
        # parse input
        args = webapi_header.set_args('orderId','productId','addflag')
        
        # arguments
        order_id = args['orderId']
        product_id = args['productId']
        addflag = args['addflag']      
        
        # check whether order was cancelled first
        status_code = webapi_header.if_cancelled(cur,order_id)
        if status_code == 1:
            return {'Bad gateway' : None}, 502
        elif status_code == 2:
            return {'Invalid order ID' : None}, 404
        elif status_code == 3:
            return {'This order was cancelled.' : None}, 404
 
        # put
        if addflag == 0:
            item_order_id = str(order_id)
            query_add = ' AND order_id IS NULL'
        else:
            item_order_id = 'NULL'
            query_add = ' AND order_id = ' + str(order_id)
        query = 'UPDATE items SET order_id = ' + item_order_id +\
                ' WHERE product_id = ' + str(product_id) +\
                query_add + ' RETURNING product_id, description'
         
        try:
            cur.execute(query)
        except:
            return {'Bad gateway' : None}, 502
            
        product_info = cur.fetchone()
        
        # cancel order if it results in no items after last put
        if addflag != 0:
            check_order_query = 'SELECT COUNT(*) FROM items WHERE order_id = ' +\
                                str(order_id)
            try:
                cur.execute(check_order_query)
            except:
                return {'Bad gateway' : None}, 502
            
            check = cur.fetchone()[0]
            if check == 0:
                cancel_query = 'UPDATE orders SET status = \'Cancelled\' ' +\
                            'WHERE order_id = ' + str(order_id)
                try:
                    cur.execute(cancel_query)
                except:
                    return {'Bad gateway' : None}, 502
        
        con.commit()
 
        con.close()

        if product_info is None:
            return {'Item not available for this order.' : None}, 404
        elif addflag == 0:
            return {'Item was added to order.' : None,
                    'Item ID:' : product_info[0],
                    'Item description:' : product_info[1]},200
        else:
            return {'Item was removed from order.' : None,
                    'Item ID:' : product_info[0],
                    'Item description:' : product_info[1]},200
    
    # cancel an order given its id
    @app.route('/orders',methods=['DELETE'])
    def delete(self):
        # connect to database
        con, cur = webapi_header.connect_to_db()
        
        # parse input
        args = webapi_header.set_args('orderId')
        
        # arguments
        order_id = args['orderId']
        
        # check whether order exists or is cancelled
        status_code = webapi_header.if_cancelled(cur,order_id)
        if status_code == 1:
            return {'Bad gateway' : None}, 502
        elif status_code == 2:
            return {'Invalid order ID' : None}, 404
        elif status_code == 3:
            return {'This order was cancelled.' : None}, 404
        
        # Cancel order
        order_query = 'UPDATE orders SET status = \'Cancelled\' ' +\
                    'WHERE order_id = ' + str(order_id) +\
                    ' RETURNING order_id'
                    
        try:
            cur.execute(order_query)
        except:
            return {'Bad gateway' : None}, 502
        
        # Change item's order_id
        item_query = 'UPDATE items SET order_id = NULL WHERE order_id = ' +\
            str(order_id)
        try:
            cur.execute(item_query)
        except:
            return {'Bad gateway' : None}, 502
        
        con.commit()
        con.close()
        
        return {'Order deleted.' : None,
                'Order ID:' : order_id},200
    
class item(Resource):
    # update item price
    @app.route('/items',methods=['PUT'])
    def put(self):
        # connect to database
        con, cur = webapi_header.connect_to_db()
        
        # parse input
        args = webapi_header.set_args('productId','unitPrice')
        
        # arguments
        product_id = args['productId']
        new_price = args['unitPrice']
        
        query = 'UPDATE items SET unit_price = ' + '{:.2f}'.format(new_price) +\
                ' WHERE product_id = ' + str(product_id) +\
                ' RETURNING product_id, description'
        try:
            cur.execute(query)
        except:
            return {'Bad gateway' : None}, 502
        
        updated_product = cur.fetchone()
        if updated_product is None:
            return {'Product does not exist.' : None}, 404
        
        con.commit()
        
        return {'Product price was updated.' : None,
                'Product ID:' : updated_product[0],
                'Product description:' : updated_product[1],
                'New Price:' : '{:.2f}'.format(new_price)},200

clubbi_api.add_resource(order, '/orders')
clubbi_api.add_resource(item,'/items')

