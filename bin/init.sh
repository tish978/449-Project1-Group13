#!/bin/sh

sqlite3 ./var/wordle-DB.db < ./share/wordle-DB_schema.sql
sqlite3 ./var/users-DB.db < ./share/users-DB_schema.sql
sqlite3 ./var/games-DB.db < ./share/games-DB_schema.sql
