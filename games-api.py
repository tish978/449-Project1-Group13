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

app = Quart(__name__)
QuartSchema(app)


app.config.from_file(f"./etc/{__name__}.toml", toml.load)


secretWord: str = ""
game_uuid: str = ""

async def _get_db():
    db = getattr(g, "_sqlite_db", None)
    if db is None:
        db = g._sqlite_db = databases.Database(app.config["DATABASES"]["URL"])
        await db.connect()
    return db

@app.route("/", methods=["GET", "POST"])
async def index():
    if request.method == "POST":
        return abort(400)
    else:
    	return textwrap.dedent(
		"""
		<h1>Welcome to Wordle Game</h1>
		<p>A prototype API for Wordle Game.</p>\n
		"""
	    )


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



@app.route("/create_new_game/", methods=["POST"])
async def create_new_game():

    db = await _get_db()

    data = await request.get_json()
    user_data = f"{data['user_id']}"
    app.logger.debug(user_data)
    entered_id = data['user_id']

    secretWord = str(random.choice(correctWords.correctWord))

    print("SECRET WORD: " + secretWord)
    game_uuid = str(uuid.uuid4())
    print("UUID GAME_ID: " + game_uuid)



    query = "INSERT INTO games (game_id, game_secret_word, won, number_of_guesses_made, number_of_guesses_left, user_id) VALUES (:game_id, :word, :won, :made, :left, :user_id)"
    await db.execute(query=query, values={"game_id": game_uuid, "word": secretWord, "won": False, "made": 0, "left": 6, "user_id": entered_id})
    return jsonify({"Success": "New Game Entered", "Game ID": game_uuid})



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
    app.logger.info(query)
    initCursor = await db.fetch_one(query=query, values={"game_id": game_id})

    if initCursor:
        guess_count = initCursor[0]
        if guess_count == 6:
            abort(505)

    sql = "SELECT game_secret_word FROM games WHERE game_id = :game_id"
    app.logger.info(query)
    cursor = await db.fetch_val(query=sql, values={"game_id": game_id})

    if cursor:
        if answer == cursor:
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
            return jsonify({"Incorrect": "Number of guesses is increased", "Number of guesses made": guess_count,
                            "Number of guesses left": guesses_left})


@app.route("/get_games_in_progress/", methods=["POST"])
async def get_games_in_progress():

    gamesList = []
    db = await _get_db()
    data = await request.get_json()
    user_data = f"{data['user_id']}"

    app.logger.debug(user_data)
    entered_id = data['user_id']
    query = "SELECT * FROM games WHERE user_id = :user_id AND won = :won"
    app.logger.info(query)
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
    app.logger.info(query)
    initCursor = await db.fetch_one(query=query, values={"game_id": entered_id})
    print("initCursor: " + str(initCursor))

    if initCursor:
        guessesMade = initCursor[4]
        won = initCursor[2]
        if won == 1:
            guessesLeft = 6 - guessesMade
            return jsonify({"Game State": "GAME OVER", "Guesses Made": guessesMade, "Guesses Left": guessesLeft})
        else:
            guessesLeft = 6 - guessesMade
            return jsonify({"Game State": "VICTORY", "Guesses Made": guessesMade, "Guesses Left": guessesLeft})
