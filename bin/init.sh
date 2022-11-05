#!/bin/sh

sqlite3 ./var/primary/mount/wordle-DB.db < ./share/wordle-DB_schema.sql
