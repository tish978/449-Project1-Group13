from quart import Quart, request, jsonify, abort, g
from quart_schema import QuartSchema  # , DataSource, validate_request
import sqlalchemy
from sqlalchemy import create_engine, insert, select, Table, Column, Integer, String, Boolean
from databases import Database
import socket
from dataclasses import dataclass
import json
import sqlite3
import correctWords
import validWords
import random
import toml
import databases
import textwrap
from quart import Quart, g, request, abort
from sqlite3 import dbapi2 as sqlite3
from quart_auth import UnauthorizedBasicAuth
from functools import wraps
from secrets import compare_digest
from typing import Any, Callable
from quart import (
    current_app,
    has_request_context,
    request,
)

app = Quart(__name__)
QuartSchema(app)

#app.config.from_file("/home/student/Documents/449-wordle/users-api.toml", toml.load)
app.config.from_file(f"./etc/{__name__}.toml", toml.load)

secretWord: str = ""


async def _get_db():
    db = getattr(g, "_sqlite_db", None)
    if db is None:
        db = g._sqlite_db = databases.Database(app.config["DATABASES"]["URL"])
        await db.connect()
    return db

@app.teardown_appcontext
async def close_connection(exception):
    db = getattr(g, "_sqlite_db", None)
    if db is not None:
        await db.disconnect()
        
async def check_auth():
    db = await _get_db()
    query = "SELECT * FROM users"
    users = await db.fetch_all(query=query,)
    user_dict = {}
    for user in users:
    	username = str(user["user_id"])
    	user_dict[username] = user["password"]
    return user_dict

def basic_auth_required(
    username_key: str = "QUART_AUTH_BASIC_USERNAME",
    password_key: str = "QUART_AUTH_BASIC_PASSWORD",
) -> Callable:
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            if has_request_context():
                auth = request.authorization
            else:
                raise RuntimeError("Not used in a valid request/websocket context")
            user = await check_auth()
            if (
                auth is not None
                and auth.type == "basic"
                and auth.username in await check_auth()
                ):
                current_app.config[password_key] = user[auth.username]
                if compare_digest(auth.password, current_app.config[password_key]):
                    return await current_app.ensure_async(func)(*args, **kwargs)
                else:
                    raise UnauthorizedBasicAuth()
            else:
                raise UnauthorizedBasicAuth()
        return wrapper
    return decorator

@app.route("/", methods=["GET", "POST"])
@basic_auth_required()
async def index():
    if request.method == "POST":
        return abort(400)
    else:
    	print("*******REQUEST: ", request.authorization)
    	return textwrap.dedent(
		"""
		<h1>Welcome to Wordle Game</h1>
		<p>A prototype API for Wordle Game.</p>\n
		"""
	    )
    
@app.route("/register/", methods=["POST"])
async def create_user():
    db = await _get_db()
    data = await request.get_json()
    print (data)

    user_data = f"{data['user_id']} {data['password']}"
    app.logger.debug(user_data)

    entered_id = data['user_id']
    entered_pass = data['password']

    query = "INSERT INTO users(user_id, password) VALUES (:user_id, :password)"

    values = {"user_id": entered_id, "password": entered_pass}
    await db.execute(query=query, values=values)

    return jsonify({"authenticated": "true"})


@app.route("/login/", methods=["POST"])
async def login():
    db = await _get_db()
    data = await request.get_json()
    user_data = f"{data['user_id']} {data['password']}"

    app.logger.debug(user_data)
    entered_id = data['user_id']
    entered_pass = data['password']

    query = "SELECT * FROM users WHERE user_id = :id and password = :password"
    app.logger.info(query)
    row = await db.fetch_one(query=query, values={"id": entered_id, "password": entered_pass})
    if row:
        return jsonify({"authenticated": "true"})
    else:
        abort(404)


@app.route("/auth/")
@basic_auth_required()
async def auth():
    db = await _get_db()
    data = await request.get_json()
    user_data = f"{data['user_id']} {data['password']}"

    app.logger.debug(user_data)
    entered_id = data['user_id']
    entered_pass = data['password']

    query = "SELECT * FROM users WHERE user_id = :id and password = :password"
    app.logger.info(query)
    row = await db.fetch_one(query=query, values={"id": entered_id, "password": entered_pass})
    if row:
        return jsonify({"authenticated": "true"})
    else:
        abort(404)
        
@app.errorhandler(404)
def not_found(e):
    return {"error": "The resource could not be found"}, 404


@app.errorhandler(505)
def not_found(e):
    return {"Error": "Game is Over"}, 505



