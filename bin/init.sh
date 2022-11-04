#!/bin/sh

sqlite3 ./var/wordle-DB.db < ./share/wordle-DB_schema.sql
