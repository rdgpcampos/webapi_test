# -*- coding: utf-8 -*-
"""
Created on Sun Jan 23 21:32:38 2022

@author: rdgpc
"""
import flask
from flask_sqlalchemy import SQLAlchemy
import os

app = flask.Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
db = SQLAlchemy(app)

class Order(db.Model):
    order_id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.String(50), unique=False, nullable=False)
    status = db.Column(db.String(50), unique=True, nullable=False)

    def __init__(self, order_id, client_id, status):
        self.order_id = order_id
        self.client_id = client_id
        self.status = status
    
   
class Item(db.Model):
  product_id = db.Column(db.Integer, primary_key=True)
  order_id = db.Column(db.Integer, nullable=True)
  description = db.Column(db.String(250), nullable=False)
  unit_price = db.Column(db.Numeric(precision=2), nullable=False)

  def __init__(self, product_id, order_id, description, unit_price):
    self.product_id = product_id
    self.order_id = order_id
    self.description = description
    self.unit_price = unit_price
    
db.create_all()

@app.route('/orders/<order_id>',methods=['GET'])
def get(order_id=-1):
    # get order
    order = Order.query.get(order_id)
    del order.__dict__['_sa_instance_state']
     
    # check if order is cancelled
    if order.__dict__['status'] == "Cancelled":
        return flask.make_response(flask.jsonify(
                 {'Order was cancelled' : None}),404)
    # check if order exists
    if len(order.__dict__) == 0:
        return flask.make_response(flask.jsonify(
                 {'Order does not exist' : None}),404)
     
    # get total price of order and include it in response
    total_price = db.select([db.func.sum(Item.items.columns.order_id)]
                           ).where(Item.items.columns.order_id == order_id)
    order.__dict__["total price" : total_price]
   
    return flask.make_response(flask.jsonify(order.__dict__),200)

@app.route('/',defaults={'path' : ''})
@app.route('/<path:prod_list>',methods=['POST'])
def post(path):
    body = flask.request.get_json()
    client_id = body['client_id']
    status = 'Released'
    db.session.add(Order(client_id,status))
    db.session.commit()
    db.session.refresh(Order(client_id,status))
    cur_order_id = Order(client_id,status).id
    for i,product in enumerate(body['product_list']):
        db.session.add()
        
        ## UPDATE..RETURNING
#result = table.update().returning(table.c.col1, table.c.col2).\
 #   where(table.c.name=='foo').values(name='bar')
#print result.fetchall()
     

