#!/bin/sh

sqlite3 ./var/users-DB < ./share/users-DB_schema.sql
sqlite3 ./var/games-DB < ./share/games-DB_schema.sql
