import sqlite3 as sql

with sql.connect("SenateBills.db") as conn:
    cursor = conn.cursor()
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS bill(
            bill_id varchar primary key,
            bill_type varchar not null,
            bill_num varchar not null,
            bill_year varchar not null,
            running varchar not null,
            bill_text varchar null,
            introduce_date date null,
            bill_nature varchar null,
            general_subject varchar null,
            specific_subject varchar null);

        CREATE TABLE IF NOT EXISTS bill_index(
            bill_id varchar not null,
            bill_index varchar not null,
            primary key (bill_id, bill_index),
            foreign key (bill_id) references bill (bill_id));

        CREATE TABLE IF NOT EXISTS author(
            author_name varchar primary key,
            author_type varchar not null,
            uf_author varchar null);

        CREATE TABLE IF NOT EXISTS authorship(
            bill_id varchar not null,
            author_name varchar not null,
            primary key (bill_id, author_name),
            foreign key (bill_id) references bill (bill_id),
            foreign key (author_name) references author (author_name));''')

    conn.commit()