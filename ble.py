from flask import Flask
from flask import render_template
from flask import request,jsonify

import datetime # Test PsycopPG2
import time
import db

app = Flask(__name__)

# debug mode!
app.debug = True
from werkzeug.debug import DebuggedApplication
app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

# @app.after_request
# def set_response_headers(response):
#     response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
#     response.headers['Pragma'] = 'no-cache'
#     response.headers['Expires'] = '0'
#     return response

@app.after_request
def add_header(response):
    response.cache_control.max_age = 0
    response.cache_control.no_cache = True
    response.cache_control.public = True
    return response

@app.route('/jinja', defaults={'path': ''})
@app.route('/jinja/<path:path>')
def route_jinja(path):
    db_connection, db_cursor = db.db_connect()
    t_wordcloud = db.db_select_word_cloud(db_connection, db_cursor)
    db.db_close(db_connection, db_cursor)

    return render_template('jinja.html', t_wordcloud=t_wordcloud)

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def route_index(path):
    time_now = time.strftime("%H:%M", time.localtime())
    return render_template('index.html', date=time_now)

@app.route('/device')
@app.route('/device/<p_limit>')
@app.route('/device/<p_address>/<p_address_type>')
def route_device(p_address=None, p_address_type=None, p_limit=100):
    time_now = time.strftime("%H:%M", time.localtime())

    db_connection, db_cursor = db.db_connect()
    t_device = db.db_select_device(db_connection, db_cursor, p_address, p_address_type, p_limit)
    db.db_close(db_connection, db_cursor)
    return render_template('device.html', date=time_now, t_device=t_device)

@app.route('/scan_data')
@app.route('/scan_data/<p_limit>')
@app.route('/scan_data/<p_address>/<p_address_type>')
def route_scan_data(p_address=None, p_address_type=None, p_limit=10):
    time_now = time.strftime("%H:%M", time.localtime())

    db_connection, db_cursor = db.db_connect()
    t_scan_data = db.db_select_scan_data(db_connection, db_cursor, p_address, p_address_type, p_limit)
    db.db_close(db_connection, db_cursor)
    return render_template('scan_data.html', date=time_now, t_scan_data=t_scan_data)

@app.route('/car')
@app.route('/scan_data_car')
def route_scan_data_car():
    time_now = time.strftime("%H:%M", time.localtime())

    db_connection, db_cursor = db.db_connect()
    t_scan_data_car = db.db_select_scan_data_car(db_connection, db_cursor)
    db.db_close(db_connection, db_cursor)
    return render_template('scan_data_car.html', date=time_now, t_scan_data_car=t_scan_data_car)

@app.route('/test/<path:subpath>')
def route_test(subpath):
    time_now = time.strftime("%H:%M", time.localtime())

    return render_template("t_" + subpath + '.html', date=time_now)

@app.route('/_add_numbers')
def add_numbers():
    a = request.args.get('a', 0, type=int)
    b = request.args.get('b', 0, type=int)
    return jsonify(result=a + b)

@app.route('/ajax', methods=['GET','POST'])
def route_ajax():
    time_now = time.strftime("%H:%M:%S", time.localtime())

    if request.method == "GET":
        params = request.args.getlist('name')
    elif request.method == "POST":
        params = request.form.getlist('name')
    else:
        params = []

    return jsonify(time=time_now, args=params)

@app.route('/ajax_db', methods=['GET','POST'])
def route_ajax_db():
    time_now = time.strftime("%H:%M:%S", time.localtime())

    if request.method == "GET":
        restrict = request.args.getlist('restrict')
        query = request.args.get('query')
    elif request.method == "POST":
        restrict = request.form.getlist('restrict')
        query = request.form.get('query')
    else:
        restrict = []
        query = ""

    t_result = []
    db_connection, db_cursor = db.db_connect()
    if query == "db_select_scan_bucket":
        t_result = db.db_select_scan_bucket(db_connection, db_cursor)
    elif query == "db_select_recap":
        t_result = db.db_select_recap(db_connection, db_cursor, restrict)

    db.db_close(db_connection, db_cursor)

    return jsonify(time=time_now, result=t_result)

if __name__ == "__main__":
        app.run(debug=True)
