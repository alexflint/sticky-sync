import os
import flask
import json
import zlib
import base64
import sqlite3
import StringIO

app = flask.Flask(__name__)

DATABASE_PATH='stickysync.sqlite3'

def get_database_conn():
    exists = os.path.exists(DATABASE_PATH)

    conn = sqlite3.connect(DATABASE_PATH)
    if not exists:
        print 'Creating table stickies'
        with conn:
            # Note that sqlite has a built-in "rowid" column that gives unique IDs
            conn.execute('CREATE TABLE stickies (user_id INTEGER, content TEXT)')

    return conn

@app.route('/update/<int:user_id>', methods=['POST'])
def serve_update_stickies(user_id):
    try:
        message = json.loads(zlib.decompress(base64.b64decode(flask.request.data)))
    except TypeError as ex:
        return flask.Response('Could not base64decode the request data', 400)
    except zlib.error as ex:
        return flask.Response('Could not unzip the request data', 400)
    except ValueError:
        return flask.Response('Could not parse the request data as json', 400)

    stickies = message['stickies']

    with get_database_conn() as conn:
        conn.execute('DELETE FROM stickies WHERE user_id=?', (user_id,))
        conn.executemany('INSERT INTO stickies(content, user_id) VALUES (?,?)',
                         zip(stickies, [user_id]*len(stickies)))

    return 'Updated %d stickies for user %d' % (len(stickies), user_id)


@app.route('/view_all/<int:user_id>')
def serve_view_all(user_id):
    conn = get_database_conn()
    c = conn.cursor()
    c.execute('SELECT content FROM stickies WHERE user_id=?', (user_id,))
    rows = c.fetchall()
    
    if len(rows) == 0:
        return flask.Response('No stickies for user %d'%user_id, 404)

    s = StringIO.StringIO()
    for row in rows:
        s.write('<pre>%s</pre>' % row[0])
        s.write('<hr>')
    return s.getvalue()


@app.route('/get/<int:user_id>')
def serve_get(user_id):
    conn = get_database_conn()
    c = conn.cursor()
    # Note that "rowid" is an sqlite3 built-in column
    c.execute('SELECT rowid,content FROM stickies WHERE user_id=?', (user_id,))
    rows = c.fetchall()
    
    if len(rows) == 0:
        return flask.Response('No stickies for user %d'%user_id, 404)

    message = [ { 'sticky_id':row[0], 'content':row[1] }
                for row in rows ]

    return json.dumps(message)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    app.run(host='0.0.0.0',  # makes it externally visible
            port=port,
            debug=True,      # code will be reloaded automatically
            )
