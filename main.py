from flask import Flask, request, send_file
import sqlite3
import os
import secrets
import time
import argparse
from werkzeug.utils import secure_filename

parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("--help", action="help", help="Show Help Message")
parser.add_argument("--init", action="store_true", help="if init the database")
parser.add_argument("--threaded", action="store_true", help="if use threaded mode")
parser.add_argument("--debug", action="store_true", help="if debug mode")
parser.add_argument("--db", "-d", default="tokenfileserver.db", help="database file name")
parser.add_argument("--folder", "-f", default="files", help="folder to store files")
parser.add_argument("--ext", "-e", default="txt, json, jpg, png, pdf", help="file extensions to allow")
parser.add_argument("--host", "-h", default="0.0.0.0", help="host to listen")
parser.add_argument("--port", "-p", default=80, help="port to listen")
args = parser.parse_args()


def init(dbname):
    if os.path.exists(dbname):
        os.remove(dbname)
    with sqlite3.connect(dbname) as connn:
        token = secrets.token_hex(16)
        connn.execute('''CREATE TABLE tokens (token text primary key, auth integer not null, expire integer not null)''')
        connn.execute('''INSERT INTO tokens (token, auth, expire) VALUES (?, 0, 0)''', (token,))
        connn.execute('''CREATE TABLE files (id integer primary key, filename text not null, realfilename text not null, token text not null, foreign key (token) references tokens(token))''')
        connn.commit()


dbname = args.db
if args.init or os.path.exists(dbname) is False:
    init(dbname)
folder = args.folder
allowed_ext = args.ext.strip().lower().split(',')
app = Flask(__name__)


def get_admin_token():
    with sqlite3.connect(dbname) as conn:
        row = conn.execute('''SELECT * FROM tokens WHERE auth = 0''').fetchone()
    return row[0]


def scan_tokens():
    with sqlite3.connect(dbname) as conn:
        rows = conn.execute('''SELECT * FROM tokens WHERE expire < ? and auth != 0''', (int(time.time()),)).fetchall()
        for row in rows:
            file_rows = conn.execute('''SELECT * FROM files WHERE token = ?''', (row[0],)).fetchall()
            for file_row in file_rows:
                if os.path.exists(os.path.join(folder, file_row[3], file_row[2])):
                    os.remove(os.path.join(folder, file_row[3], file_row[2]))
            conn.execute('''DELETE FROM files WHERE token = ?''', (row[0],))
            if os.path.exists(os.path.join(folder, row[0])):
                os.rmdir(os.path.join(folder, row[0]))
            conn.execute('''DELETE FROM tokens WHERE token = ?''', (row[0],))


def get_auth(t):
    scan_tokens()
    if t is None:
        return -1
    with sqlite3.connect(dbname) as conn:
        row = conn.execute('''SELECT * FROM tokens WHERE token = ?''', (t,)).fetchone()
    if row is None:
        return -1
    return int(row[1])


def get_new_token():
    with sqlite3.connect(dbname) as conn:
        token = secrets.token_hex(16)
        while conn.execute('''SELECT * FROM tokens WHERE token = ?''', (token,)).fetchone() is not None:
            token = secrets.token_hex(16)
    return token


def get_file_name(t):
    with sqlite3.connect(dbname) as conn:
        filename = secrets.token_hex(8)
        while conn.execute('''SELECT * FROM files WHERE filename = ? and token = ?''', (filename, t)).fetchone() is not None:
            filename = secrets.token_hex(8)
    return filename


def is_file_allowed(filename):
    ext = filename.rsplit('.')[-1].lower()
    return ext in allowed_ext


@app.route('/')
def index():
    return 'Token File Server\n'


@app.route('/renew')
def renew():
    t = request.headers.get('Authorization')
    a = get_auth(t)
    if a != 0:
        return {'msg': 'invalid operation'}
    token = get_new_token()
    with sqlite3.connect(dbname) as conn:
        conn.execute('''UPDATE tokens SET token = ? WHERE token = ?''', (token, t))
        conn.commit()
    return {'msg': 'ok', 'token': token}


@app.route('/create')
def create():
    t = request.headers.get('Authorization')
    a = get_auth(t)
    if a != 0 and a != 1:
        return {'msg': 'invalid operation'}
    expire = request.args.get('expire')
    if expire is None:
        return {'msg': 'invalid operation'}
    auth = request.args.get('auth')
    if auth is None:
        auth = 2
    auth = int(auth)
    if auth != 1 or auth != 2:
        auth = 2
    token = get_new_token()
    expire = int(time.time()) + int(expire)
    with sqlite3.connect(dbname) as conn:
        conn.execute('''INSERT INTO tokens (token, auth, expire) VALUES (?, ?, ?)''', (token, auth, expire))
        conn.commit()
    return {'msg': 'ok', 'token': token}


@app.route('/invalidate')
def invalidate():
    t = request.headers.get('Authorization')
    a = get_auth(t)
    if a == 0 or a == -1:
        return {'msg': 'invalid operation'}
    with sqlite3.connect(dbname) as conn:
        conn.execute('''UPDATE tokens SET expire = 0 WHERE token = ?''', (t,))
        conn.commit()
    scan_tokens()
    return {'msg': 'ok'}


@app.route('/upload', methods=['POST'])
def upload():
    t = request.headers.get('Authorization')
    a = get_auth(t)
    if a == -1:
        return {'msg': 'invalid operation'}
    file = request.files['file']
    if file is None:
        return {'msg': 'invalid file'}
    filename = file.filename
    if is_file_allowed(filename) is False:
        return {'msg': 'invalid file extension'}
    filename = secure_filename(filename)
    realfilename = get_file_name(t)
    if os.path.exists(os.path.join(folder, t)) is False:
        os.makedirs(os.path.join(folder, t))
    filepath = os.path.join(folder, t, realfilename)
    file.save(filepath)
    with sqlite3.connect(dbname) as conn:
        conn.execute('''INSERT INTO files (filename, realfilename, token) VALUES (?, ?, ?)''', (filename, realfilename, t))
        conn.commit()
    return {'msg': 'ok', 'filename': realfilename}


@app.route('/download/<filename>')
def download(filename):
    t = request.headers.get('Authorization')
    a = get_auth(t)
    if a == -1:
        return {'msg': 'invalid operation'}
    with sqlite3.connect(dbname) as conn:
        row = conn.execute('''SELECT * FROM files WHERE realfilename = ? and token = ?''', (filename, t)).fetchone()
    if row is None:
        return {'msg': 'file not found'}
    filepath = os.path.join(folder, t, row[2])
    if os.path.exists(filepath) is False:
        return {'msg': 'file not found'}
    return send_file(filepath, download_name=row[1], as_attachment=True)


if __name__ == '__main__':
    print('admin token:', get_admin_token())
    app.run(host=args.host, port=args.port, debug=args.debug, threaded=args.threaded)
