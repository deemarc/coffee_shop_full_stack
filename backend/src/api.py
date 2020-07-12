import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS
import sys

from .database.models import db_drop_and_create_all, setup_db, Drink, db
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@DONE uncomment the following line to initialize the datbase
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

## ROUTES
'''
@DONE implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks", methods=['GET'])
def get_drinks():
    error = False
    try:
        drinks = Drink.query.all()
        drinks_short = [drink.short() for drink in drinks]
    
    except Exception as err:
        app.logger.error(err)
        error = True
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        abort(500)
        
    return jsonify({"sucess":True,"drinks":drinks_short})

'''
@DONE implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks-detail", methods=['GET'])
@requires_auth('get:drinks-detail')
def get_drinks_detail(payload):
    app.logger.info(f"payload:{payload}")
    error = False
    try:
        drinks = Drink.query.all()
        drinks_long = [drink.long() for drink in drinks]
        
    
    except Exception as err:
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        abort(500)
        
    return jsonify({"sucess":True,"drinks":drinks_long})

'''
@DONE implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks", methods=['POST'])
@requires_auth('post:drinks')
def post_drink(payload):
    app.logger.info(f"payload:{payload}")
    error = False

    json_data = request.get_json()
    if not json:
        return jsonify({"status":"fail", "messagge":"recive empty body"}),400
    data = {}
    title = json_data.get('title',None)
    if not title:
        return jsonify({"status":"fail", "message":"there is no title in the given body to create a drink"}), 400
    else:
        data['title'] = title
    
    recipe = json_data.get('recipe',None)
    if recipe:
        if not isinstance(recipe, list):
            recipe = [recipe]
        data['recipe'] = json.dumps(recipe)
    
    app.logger.info(f"current title:{title}, recipe:{recipe}")

    drink = Drink.query.filter_by(title=data['title']).first()
    if drink:
        # drink with given title is already exist
        abort(400)

    try:
        new_drink = Drink(**data)
        new_drink.insert()
        new_drink_str = new_drink.long()

    except Exception:
        error = True
        errMsg = sys.exc_info()
        app.logger.error(errMsg)
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        abort(500)
        
    return jsonify({"sucess":True,"drinks":new_drink_str})

'''
@DONE implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks/<id>", methods=['PATCH'])
@requires_auth('patch:drinks')
def patch_drink(payload, id):
    app.logger.info(f"payload:{payload}")
    error = False

    drink = Drink.query.filter_by(id=id).first()
    if not drink:
        abort(404)
    try:
        json_data = request.get_json()
        title = json_data.get('title',None)
        recipe = json_data.get('recipe',None)
        if title:
            drink.title = title
        if recipe:
            if not isinstance(recipe, list):
                recipe = [recipe]
            drink.recipe = recipe
        drink.update()
        drink_list = [drink.long()]
    except Exception as err:
        error = True
        app.logger.error(f"err:{err}")
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        print("+++++++++++ get into error")
        abort(500)
        
    return jsonify({"sucess":True,"drinks":drink_list})


'''
@DONE implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''
@app.route("/drinks/<id>", methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, id):
    app.logger.info(f"payload:{payload}")
    error = False
    drink = Drink.query.filter_by(id=id).first()
    if not drink:
        abort(404)

    try:
        drink.delete()

    except Exception as err:
        error = True
        app.logger.error(f"err:{err}")
        db.session.rollback()
    finally:
        db.session.close()

    if error:
        abort(500)
        
    return jsonify({"sucess":True,"message":f"drink id:{id} has been deleted successfully"})

## Error Handling

@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": "bad request"
    }), 400

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": "Unauthorized"
    }), 401

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404

@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": "Internal Server Error"
    }), 500
    
'''

@DONE implement error handler for AuthError
    error handler should conform to general task above 
'''
