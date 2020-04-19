import aiohttp
import asyncio
import requests as req
import sqlite3
from bs4 import BeautifulSoup

def get_text_alt(elem, tag, alt=None):
	try:
		return elem.find(tag).text
	except AttributeError:
		return alt

def get_bills_list(n_chunks):
    page = req.get('http://legis.senado.leg.br/dadosabertos/materia/legislaturaatual').text
    soup = BeautifulSoup(page, 'lxml')
    chunks = []
    for bill in soup.findAll('codigomateria'):
        bill = bill.text
        if len(chunks) < n_chunks:
            chunks.append(bill)
            continue

        yield chunks
        chunks = [bill]

def insert_bills(bill, conn):
    cursor = conn.cursor()
    sql_command = ''' INSERT INTO bill VALUES (?,?,?,?,?,?,?,?,?,?)'''
    cursor.execute(sql_command, bill)

def insert_author(author, conn):
    cursor = conn.cursor()
    sql_command = ''' INSERT INTO author VALUES (?,?,?)'''
    try:
        cursor.execute(sql_command, author)

    except sqlite3.IntegrityError:
        pass

def insert_authorship(authorship, conn):
    cursor = conn.cursor()
    sql_command = ''' INSERT INTO authorship VALUES (?,?)'''
    cursor.execute(sql_command, authorship)

def insert_index(index, conn):
    cursor = conn.cursor()
    sql_command = ''' INSERT INTO bill_index VALUES (?,?)'''
    try:
        cursor.executemany(sql_command, index)

    except sqlite3.IntegrityError:
        for i in index:
            try:
                cursor.execute(sql_command, i)

            except sqlite3.IntegrityError:
                continue

def extract_index(index):
    splited = index.split(',')
    clear_splited = list(map(lambda x:x.replace('[',''), splited))
    clear_splited = list(map(lambda x:x.replace(']',''), clear_splited))
    clear_splited = list(map(lambda x:x.strip(), clear_splited))
    return clear_splited

def extract_info(bill_chunk):
    conn = sqlite3.connect('SenateBills.db')
    for bill in bill_chunk:
        bill_id = get_text_alt(bill, 'codigomateria')
        
        if bill_id == None:
            continue

        bill_info = (
            bill_id,
            get_text_alt(bill, 'descricaosubtipomateria'),
            get_text_alt(bill, 'numeromateria'),
            get_text_alt(bill, 'anomateria'),
            get_text_alt(bill, 'indicadortramitando'),
            get_text_alt(bill, 'ementamateria'),
            get_text_alt(bill, 'dataapresentacao'),
            get_text_alt(bill, 'descricaonatureza'),
            get_text_alt(bill, 'assuntogeral'),
            get_text_alt(bill, 'assuntoespecifico')
        )

        insert_bills(bill_info, conn)

        index = extract_index(get_text_alt(bill, 'indexacaomateria', 'none'))
        index_info = [(bill_id, i) for i in index]
        print(index_info)
        print('______________________________')
        insert_index(index_info, conn)

        for author in bill.findAll('autor'):
            author_name = author.find('nomeautor').text
            author_info = (
                    author_name, 
                    get_text_alt(author, 'descricaotipoautor'),
                    get_text_alt(author, 'ufautor')
                )

            authorship_info = (bill_id, author_name)
            print(author_info)
            insert_author(author_info, conn)
            insert_authorship(authorship_info, conn)

    conn.commit()
    conn.close()

async def fetch(session, url):
    async with session.get(url) as response:
        return BeautifulSoup(await response.text(), 'lxml')

async def get_bills(chunks):
    async with aiohttp.ClientSession() as session:
        url = 'http://legis.senado.leg.br/dadosabertos/materia/{}'
        bills_chunks = [fetch(session, url.format(bill)) for bill in chunks]
        return await asyncio.gather(*bills_chunks)

loop = asyncio.get_event_loop()
chunks = get_bills_list(20)
while True:
    try:
        bills = loop.run_until_complete(get_bills(next(chunks)))
        extract_info(bills)
        continue

    except StopIteration:
        break
        loop.close()
