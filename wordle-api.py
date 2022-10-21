from quart import Quart, request, jsonify, abort
from quart_schema import QuartSchema #, DataSource, validate_request
import sqlalchemy
from sqlalchemy import create_engine, insert, select, Table, Column, Integer, String, Boolean
from databases import Database
import socket
from dataclasses import dataclass
import json
import wget
import sqlite3
import correctWords
import validWords
import random


db = Database('sqlite:////home/student/Documents/449-wordle/wordle-DB')


app = Quart(__name__)
QuartSchema(app)

secretWord: str = ""


@app.errorhandler(404)
def not_found(e):
    return {"error": "The resource could not be found"}, 404

@app.route("/")
async def index():
    return "hello"


@app.route("/register", methods=["POST"])
async def create_user():
    data = await request.get_json()

    user_data = f"{data['user_id']} {data['password']}"
    app.logger.debug(user_data)
    
    entered_id = data['user_id']
    entered_pass = data['password']
    
    query = "INSERT INTO users(user_id, password) VALUES (:user_id, :password)"
  

    values = {"user_id": entered_id, "password": entered_pass}
    await db.execute(query=query, values=values)

    return jsonify({"authenticated": "true"})


@app.route("/login", methods=["POST"])
async def login():
    data = await request.get_json()
    user_data = f"{data['user_id']} {data['password']}"

    app.logger.debug(user_data)
    entered_id = data['user_id']
    entered_pass = data['password']
    
    query = "SELECT * FROM users WHERE user_id = :id and password = :password"
    row = await db.execute(query=query, values={"id": entered_id, "password": entered_pass})
    if row:
    	return jsonify({"authenticated": "true"})
    

    

@app.route("/login/<int:id><string:password>", methods=["GET"])
async def login_user(id, password):
    db = await request.get_json()
    book = await db.fetch_one("SELECT * FROM users WHERE user_id = :user_id AND password = :password", values={"user_id": id, "password": password})
    if book:
        return jsonify({"authenticated": "true"})
    else:
        abort(404)
        
        
        

@app.route("/create_new_game/<int:id>", methods=["POST"])
async def create_new_game(id):


    secretWord = str(random.choice(correctWords.correctWord))
    print("SECRET WORD: " + secretWord)


    query = "INSERT INTO games (game_id, game_secret_word, won, number_of_guesses_made, number_of_guesses_left, user_id) VALUES (NULL, :word, :won, :made, :left, :user_id)"
    await db.execute(query=query, values={"word": secretWord, "won": False, "made": 0, "left": 6, "user_id": id})
    return jsonify({"Success": "New Game Entered"})





@app.route("/word_load/", methods=["POST"])
async def correct_word_load():

    for word in correctWords.correctWord:
        query = "INSERT INTO correctWords (correct_word_id, correct_word, game_id) VALUES (NULL, :correctWord, NULL)"
        await db.execute(query=query,
                         values={"correctWord": word})

    return "All correct words loaded into DB"
    
    
    
    

@app.route("/valid_word_load/", methods=["POST"])
async def valid_word_load():

    for word in validWords.validWord:
        query = "INSERT INTO validWords (valid_word_id, valid_word, game_id) VALUES (NULL, :validWord, NULL)"
        await db.execute(query=query,
                         values={"validWord": word})

    return "All valid words loaded into DB"



@app.route('/answer/', methods=['POST'])
async def answer():

    guess_count: int = 0
    
    data = await request.get_json()
    user_data = f"{data['game_id']} {data['answer']}"

    app.logger.debug(user_data)
    game_id = data['game_id']
    answer = data['answer']
    if len(answer) > 5:
    		abort(404)
    

    connection = sqlite3.connect("////home/student/Documents/449-wordle/wordle-DB")
    print("DB connected")
    guessCheck = "SELECT number_of_guesses_made FROM games WHERE game_id = ?"
    initCursor = connection.execute(guessCheck, [game_id])
    for guessMade in initCursor:
    	guess_count = guessMade[0]
    	if guess_count == 6:
    		abort(404) 

    
    sql = "SELECT game_secret_word FROM games WHERE game_id = ?"
    cursor = connection.execute(sql, [game_id])
    for row in cursor:
    	if answer == row[0]:
    		guess_count = guess_count + 1
    		count_update = "UPDATE games SET number_of_guesses_made=:guess_count WHERE game_id=:game_id"
    		await db.execute(query=count_update, values={"guess_count": guess_count, "game_id": game_id})
    		return jsonify({"VICTORY": "Correct word!"})
    	else:
    		guess_count = guess_count + 1
    		count_update = "UPDATE games SET number_of_guesses_made=:guess_count WHERE game_id=:game_id"
    		await db.execute(query=count_update, values={"guess_count": guess_count, "game_id": game_id})
    		return jsonify({"Incorrect": "Number of guesses is increased."})
    	


@app.route("/DB")
async def db_connect():

    connection = await db.connect()
    print("connection: " + str(connection))
    return str(connection)

app.run()

