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
            conn.execute('CREATE TABLE stickies (sticky_id INT PRIMARY KEY, user_id INT, content TEXT)')

    return conn

@app.route('/update/<int:user_id>', methods=['POST'])
def serve_update_stickies(user_id):
    try:
        datastr = zlib.decompress(base64.b64decode(flask.request.data))
        data = json.loads(datastr)
        stickies = data['stickies']

        with get_database_conn() as conn:
            conn.execute('DELETE FROM stickies WHERE user_id=?', (user_id,))
            conn.executemany('INSERT INTO stickies(content, user_id) VALUES (?,?)',
                             zip(stickies, [user_id]*len(stickies)))

        return 'Updated %d stickies for user %d' % (len(stickies), user_id)

    except zlib.error as ex:
        return flask.Response('Could not decompress (unzip) the data', 400)
    except TypeError as ex:
        return flask.Response('Could not base64decode the request data', 400)

@app.route('/view_all/<int:user_id>')
def serve_view_all(user_id):
    conn = get_database_conn()
    c = conn.cursor()
    c.execute('SELECT content FROM stickies WHERE user_id=?', (user_id,))

    s = StringIO.StringIO()
    rows = c.fetchall()
    print 'Got %d rows' % len(rows)
    for row in rows:
        s.write('<pre>%s</pre>' % row[0])
        s.write('<hr>')
    return s.getvalue()


if __name__ == '__main__':
    port = int(os.environ.get('PORT', '5000'))
    app.run(host='0.0.0.0',  # makes it externally visible
            port=port,
            debug=True,      # code will be reloaded automatically
            )
