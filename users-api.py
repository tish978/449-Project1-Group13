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

app = Quart(__name__)
QuartSchema(app)

app.config.from_file("/home/student/Documents/449-wordle/users-api.toml", toml.load)

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


@app.errorhandler(404)
def not_found(e):
    return {"error": "The resource could not be found"}, 404


@app.errorhandler(505)
def not_found(e):
    return {"Error": "Game is Over"}, 505


@app.route("/register/", methods=["POST"])
async def create_user():
    db = await _get_db()
    data = await request.get_json()

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

@app.route("/auth", methods=["POST"])
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



