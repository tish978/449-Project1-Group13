from quart import Quart, request, jsonify, abort, g
from quart_schema import QuartSchema #, DataSource, validate_request
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


app.config.from_file("/home/student/Documents/449-wordle/wordle-api.toml", toml.load)


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
    row = await db.fetch_one(query=query, values={"id": entered_id, "password": entered_pass})
    if row:
    	return jsonify({"authenticated": "true"})  
    else:
    	abort(404)
    


@app.route("/create_new_game/", methods=["POST"])
async def create_new_game():
    db = await _get_db()
    
    
    data = await request.get_json()
    user_data = f"{data['user_id']}"
    app.logger.debug(user_data)
    entered_id = data['user_id']
    
   
    secretWord = str(random.choice(correctWords.correctWord))
    print("SECRET WORD: " + secretWord)


    query = "INSERT INTO games (game_id, game_secret_word, won, number_of_guesses_made, number_of_guesses_left, user_id) VALUES (NULL, :word, :won, :made, :left, :user_id)"
    await db.execute(query=query, values={"word": secretWord, "won": False, "made": 0, "left": 6, "user_id": entered_id})
    return jsonify({"Success": "New Game Entered"})



  
@app.route("/word_load/", methods=["POST"])
async def correct_word_load():
    db = await _get_db()

    for word in correctWords.correctWord:
        query = "INSERT INTO correctWords (correct_word_id, correct_word, game_id) VALUES (NULL, :correctWord, NULL)"
        await db.execute(query=query,
                         values={"correctWord": word})

    return jsonify({"Success":"All correct words loaded into DB"})    
    



@app.route("/valid_word_load/", methods=["POST"])
async def valid_word_load():

    db = await _get_db()

    for word in validWords.validWord:
        query = "INSERT INTO validWords (valid_word_id, valid_word, game_id) VALUES (NULL, :validWord, NULL)"
        await db.execute(query=query,
                         values={"validWord": word})

    return jsonify({"Success":"All valid words loaded into DB"}) 




@app.route('/answer/', methods=['POST'])
async def answer():
    db = await _get_db()
    guess_count: int = 0
    guesses_left: int = 0
    
    data = await request.get_json()
    user_data = f"{data['game_id']} {data['answer']}"

    app.logger.debug(user_data)
    game_id = data['game_id']
    answer = data['answer']
    if len(answer) > 5:
    		abort(404)
    
 
    query = "SELECT number_of_guesses_made FROM games WHERE game_id = :game_id"
    initCursor = await db.fetch_one(query=query, values={"game_id": game_id})
    #for guessMade in initCursor:
    if initCursor:
    	print("guess_count: " + str(guess_count))
    	print("initCursor " + str(initCursor))
    	guess_count = initCursor[0]
    	if guess_count == 6:
    		abort(505) 

    
    sql = "SELECT game_secret_word FROM games WHERE game_id = :game_id"
    cursor = await db.fetch_val(query=sql, values={"game_id": game_id})
    #for row in cursor:
    	#if answer == row[0]:
    if cursor:
    	print("cursor: " + str(cursor))
    	if answer == cursor:
    	   print("yes")
    	   guess_count = guess_count + 1
    	   guesses_left = 6 - guess_count
    	   count_update = "UPDATE games SET number_of_guesses_made=:guess_count WHERE game_id=:game_id"
    	   await db.execute(query=count_update, values={"guess_count": guess_count, "game_id": game_id})
    	   guesses_left_update = "UPDATE games SET number_of_guesses_left=:guesses_left WHERE game_id=:game_id"
    	   await db.execute(query=guesses_left_update, values={"guesses_left": guesses_left, "game_id": game_id})
    	   victory_update = "UPDATE games SET won=:won WHERE game_id=:game_id"
    	   await db.execute(query=victory_update, values={"won": 1, "game_id": game_id})
    	   return jsonify({"VICTORY": "Correct word!"})
    	else:
    	   guess_count = guess_count + 1
    	   guesses_left = 6 - guess_count
    	   count_update = "UPDATE games SET number_of_guesses_made=:guess_count WHERE game_id=:game_id"
    	   await db.execute(query=count_update, values={"guess_count": guess_count, "game_id": game_id})
    	   guesses_left_update = "UPDATE games SET number_of_guesses_left=:guesses_left WHERE game_id=:game_id"
    	   await db.execute(query=guesses_left_update, values={"guesses_left": guesses_left, "game_id": game_id})
    	   return jsonify({"Incorrect": "Number of guesses is increased", "Number of guesses made": guessCount, "Number of guesses left": guesses_left})




@app.route("/get_games_in_progress/", methods=["POST"])
async def get_games_in_progress():

    gamesList = []

    db = await _get_db()
    data = await request.get_json()
    user_data = f"{data['user_id']}"

    app.logger.debug(user_data)
    entered_id = data['user_id']

    
    query = "SELECT * FROM games WHERE user_id = :user_id AND won = :won"
    initCursor = await db.fetch_all(query=query, values={"user_id": entered_id, "won": 0})
    for game in initCursor:
    	id_of_game = game[0]
    	gamesList.append(id_of_game)
    	 
    if len(gamesList) == 0:
    	abort(404)
    else:
    	return jsonify({"Games in Progress": gamesList})
    	
    	

@app.route("/get_game_state/", methods=["POST"])
async def get_game_state():

    guessesLeft: int = 0
    guessesMade: int = 0

    db = await _get_db()
    data = await request.get_json()
    user_data = f"{data['game_id']}"

    app.logger.debug(user_data)
    entered_id = data['game_id']

    query = "SELECT * FROM games WHERE game_id = :game_id"
    initCursor = await db.fetch_one(query=query, values={"game_id": entered_id})
    if initCursor:
    	guessesMade = initCursor[3]
    	won = initCursor[2]
    	if won == 1:
    		guessesLeft = 6 - guessesMade
    		return jsonify({"Game State": "GAME OVER", "Guesses Made": guessesMade, "Guesses Left": guessesLeft})
    	else:
    		guessesLeft = 6 - guessesMade
    		return jsonify({"Guesses Made": guessesMade, "Guesses Left": guessesLeft})    	


@app.route("/DB")
async def db_connect():

    connection = await db.connect()
    print("connection: " + str(connection))
    return str(connection)

app.run()
