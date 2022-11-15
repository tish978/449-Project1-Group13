#!/bin/sh

sqlite3 ./var/primary/mount/wordle-DB.db < ./share/wordle-DB_schema.sql
sqlite3 ./var/primary/mount/users-DB.db < ./share/users-DB_schema.sql
sqlite3 ./var/primary/mount/games-DB.db < ./share/games-DB_schema.sql
