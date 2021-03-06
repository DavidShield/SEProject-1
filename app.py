#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
from analyzer import analyzeSymbol

try:
    import mysql.connector  # using mysql connector should install it first(python 2.7/3.3/3.4)
except ImportError:
    print('Please Install MySQL Connector(Python) First.')
    raise SystemExit()
try:
    from yahoo_finance import Share
except ImportError:
    import pip

    pip.main(['install', 'yahoo_finance'])
    from yahoo_finance import Share

try:
    import pandas as pd
    from pandas import DataFrame
except ImportError:
    import pip

    pip.main(['install', 'pandas'])
    import pandas as pd

try:
    import pandas_datareader as pdr
    from pandas_datareader import data, wb
except ImportError:
    import pip

    pip.main(['install', 'pandas_datareader'])
    import pandas_datareaders as pdr
    from pandas_datareaders import data, wb

try:
    from sqlalchemy import create_engine
except ImportError:
    import pip

    pip.main(['install', 'sqlalchemy'])
    from sqlalchemy import create_engine

try:
    from datetime import *
except ImportError:
    import pip

    pip.main(['install', 'datetime'])
    from datetime import *

import time
import base64
import random
import hmac
import time
import json
import os
import codecs
from io import StringIO



try:
    from flask import Flask, request, redirect, make_response, render_template
except ImportError:
    import pip

    pip.main(['install', 'flask'])
    from flask import Flask, request, redirect, make_response, render_template

try:
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter
    import matplotlib.pyplot as plt
except ImportError:
    import pip

    pip.main(['install', 'matplotlib'])
    from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
    from matplotlib.figure import Figure
    from matplotlib.dates import DateFormatter
    import matplotlib.pyplot as plt

PassWord = 'fflovexx123'
User = 'root'
Host = '127.0.0.1'
Port = '3306'
Database = 'SEProject'

try:
    cnx = mysql.connector.connect(user=User, password=PassWord, host=Host)  # using configuration of sever
except mysql.connector.Error:
    print('Can Not Connect With Database Sever.')
    raise SystemExit()

cursor = cnx.cursor()
# using mysql to create real time data
create_Login_info = '''CREATE TABLE IF NOT EXISTS login_info               
                       (
                          `user_name` CHAR(20),
                          `password` CHAR(20),
                          `email` CHAR(20),
                          PRIMARY KEY(user_name)
                         );'''
cursor.execute('CREATE DATABASE IF NOT EXISTS ' + Database)  # creat database if not exists
cursor.execute('USE ' + Database)  # select the database
cursor.execute(create_Login_info)  # create table
db = SQLAlchemy()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://{__user__}:{__password__}@{__host__}:{__port__}/{__db_name__}'.format(
    __password__=PassWord,
    __user__=User,
    __host__=Host,
    __port__=Port,
    __db_name__=Database,
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)


login_uri = 'http://127.0.0.1:5000/client/passport'
register_uri = 'http://127.0.0.1:5000/register'
user = ' '
auth_code = {}  # use a dict to store authorization code
oauth_redirect_uri = []

TIME_OUT = 3600 * 2


def find_p(user_name):
    find_password = '''SELECT login_info.password
                     FROM login_info
                     WHERE EXISTS(SELECT *
                                  WHERE login_info.user_name=\'''' + user_name + '\');'
    cursor.execute(find_password)
    p = cursor.fetchall()
    return p


def find_e(email):
    find_email = '''SELECT *
                  FROM login_info
                  WHERE login_info.email=\'''' + email + '\';'
    cursor.execute(find_email)
    e = cursor.fetchall()
    return e


def gen_token(data):  # generalize token

    '''

    :param data: dict type
    :return: base64 str
    '''

    data = data.copy()

    if "salt" not in data:
        data["salt"] = unicode(random.random()).decode("ascii")
    if "expires" not in data:
        data["expires"] = time.time() + TIME_OUT

    payload = json.dumps(data).encode("utf-8")  # dict to json str

    # generalize signature
    sig = _get_signature(payload)  # generalize 16-bit string
    return encode_token_bytes(payload + sig)  # json str + signature = new token  32-bit str


# this function is to generalize authorization code which in this case is just a random number
def gen_auth_code(uri, user_id):  # when verify code, uri is needed as well
    code = random.randint(0, 10000)
    auth_code[code] = [uri, user_id]
    return code  # authorization code


def verify_token(token):  # verify token
    '''

    :param token: base64 str
    :return: dict type
    '''
    decode_token = decode_token_bytes(str(token))  # base64 after decode
    payload = decode_token[:-16]  # start to 16th last element (uid+random+time) json string
    sig = decode_token[-16:]  # 16th last to the end (sig)

    # generalize signature
    expected_sig = _get_signature(payload)
    if sig != expected_sig:
        return {}
    data = json.loads(payload.decode("utf-8"))  # if token is correct, json str to dict
    if data.get("expires") >= time.time():  # if token not expired
        return data
    return 0


def _get_signature(value):  # HMAC ALGORITHM
    """Calculate the HMAC signature for the given value(any string)."""
    return hmac.new('secret123456', value).digest()


def encode_token_bytes(data):
    return base64.urlsafe_b64encode(data)


def decode_token_bytes(data):
    return base64.urlsafe_b64decode(data)


# verification-server-side:
@app.route('/index', methods=['POST', 'GET'])
def index():
    # print request.headers # print acquired headers to console
    print(request.headers)
    return "Hello"


# verify user's username and password correct or not,if correct return user a token
@app.route('/login', methods=['POST', 'GET'])
def login():
    # request's header to store user's uid and pw
    uid, pw = base64.b64decode(request.headers['Authorization'].split(' ')[-1]).split(':')
    if find_p(uid) and find_p(uid)[0][0].encode("ascii") == pw:
        return gen_token(dict(user=uid, pw=pw))
    else:
        return redirect(login_uri);


# this function is to handle all the stuff with login verification
# it needs to check if the authorization code and uri redirection are correct or not
# if all the requirements match, then release the token
@app.route('/oauth', methods=['POST', 'GET'])
def oauth():
    # handle form login, and set Cookie meanwhile
    if request.method == 'POST' and request.form['username']:
        if request.args.get('redirect_uri') == login_uri:
            u = request.form['username']
            p = request.form['password']
            if find_p(u) and find_p(u)[0][0].encode("ascii") == p and oauth_redirect_uri:
                expire_date = datetime.utcnow() + timedelta(minutes=10)
                uri = oauth_redirect_uri[0] + '?code=%s' % gen_auth_code(oauth_redirect_uri[0], u)
                resp = make_response(redirect(uri))
                resp.set_cookie('login', '_'.join([u, p]), expires=expire_date)
                user = u
                return resp
            else:

                return render_template("login.html", alert='Invalid Username or Password!')
        elif request.args.get('redirect_uri') == register_uri:
            u = request.form['username']
            p1 = request.form['password1']
            p2 = request.form['password2']
            email = request.form['E-mail']
            if not find_p(u):
                if not find_e(email):
                    if p1 == p2:
                        cursor.execute('INSERT INTO login_info (user_name,password,email) VALUES (%s, %s,%s);',
                                       (u, p1, email))
                        cnx.commit()
                        resp = make_response(redirect('http://127.0.0.1:5000/client/login'))
                        resp.set_cookie('login', expires=0)
                        return resp
                    else:
                        return render_template("register.html", alert='Passwords are Differents!')
                else:
                    return render_template("register.html", alert='The Email has already been Registered')
            else:
                return render_template("register.html", alert='The Username has already been Used')
    # verify authorization code and release token
    if request.args.get('code'):
        auth_info = auth_code.get(int(request.args.get('code')))  # code = redirect_uri + user
        if auth_info[0] == request.args.get('redirect_uri'):
            # store user in auth_code of authorization code and package it in the token
            target1 = 'http://127.0.0.1:5000/logined?token=%s' % gen_token(
                dict(user=request.args.get('user'), user_id=auth_info[1]))
            return redirect(target1)  # gen_token(dict(user=request.args.get('user'), user_id=auth_info[1]))

    # if current login user has Cookie, skip verification, otherwise fill the form
    if request.args.get('redirect_uri'):
        oauth_redirect_uri.append(request.args.get('redirect_uri'))
        if request.args.get('redirect_uri') == register_uri:
            return render_template("register.html")
        elif request.args.get('redirect_uri') == login_uri:
            if request.cookies.get('login'):
                u, p = request.cookies.get('login').split('_')
                if find_p(u) and find_p(u)[0][0].encode("ascii") == p:
                    uri = oauth_redirect_uri[0] + '?code=%s' % gen_auth_code(oauth_redirect_uri[0], u)
                    return redirect(uri)
                else:
                    return redirect(login_uri)
            return render_template("login.html")

            # if request.args.get('redirect_uri'):
            #     oauth_redirect_uri.append(request.args.get('redirect_uri'))
            # if request.args.get('username'):
            #     if users.get(request.args.get('username'))[0] == request.args.get('password') and oauth_redirect_uri:  # user offers pw
            #         uri = oauth_redirect_uri[0] + '?code=%s' % gen_auth_code(oauth_redirect_uri[0])  # if pw, offer auth_code
            #         return redirect(uri)   # this redirect is to check the code see in next if
            # if request.args.get('code'):    # to check the request has auth code and earlier offered redirect_uri or not
            #     if auth_code.get(int(request.args.get('code'))) == request.args.get('redirect_uri'):
            #         return gen_token(request.args.get('user'))  # if no problem, give client the token
            # return 'please login'


# client-side:
# this function is to redirect all the requests sent to /client/login to http://localhost:5000/oauth
@app.route('/client/login', methods=['POST', 'GET'])
def client_login():
    uri = 'http://127.0.0.1:5000/oauth?response_type=code&user=%s&redirect_uri=%s' % (user, login_uri)
    return redirect(uri)


@app.route('/client/passport', methods=['POST', 'GET'])
def client_passport():
    code = request.args.get('code')
    uri = 'http://127.0.0.1:5000/oauth?grant_type=authorization_code&code=%s&redirect_uri=%s&user=%s' \
          % (code, login_uri, user)
    return redirect(uri)


@app.route('/client/register', methods=['POST', 'GET'])
def client_register():
    uri = 'http://127.0.0.1:5000/oauth?response_type=code&user=%s&redirect_uri=%s' % (user, register_uri)
    return redirect(uri)


@app.route('/home', methods=['POST', 'GET'])
def home():
    if request.method == 'POST' and request.form['stock']:
        stock = request.form['stock']
        username = request.cookies.get('login').split('_')[0]
        uri = 'http://127.0.0.1:5000/stock?username=%s&stock_name=%s' % (username, stock)
        return redirect(uri)
    if request.cookies.get('login'):
        u, p = request.cookies.get('login').split('_')
        if find_p(u) and find_p(u)[0][0].encode("ascii") == p:
            '<head><style id="jsbin-css">.login{display:none;} .logout{display:inline}'
            return render_template('home.html', change='change')
    return render_template('home.html')


@app.route('/stock', methods=['POST', 'GET'])
def stock():
    data_types = [
        'High',
        'Low',
        'Close',
        'Volume',
        'Adj Close',
    ]
    stockname = request.args.get('stock_name')

    window = 50
    window2 = 150

    recent_trend_query = """
    SELECT Date, `{__value_name__}`
    FROM seproject.historicaldata
    where sym = '{__stockname__}'
    order by Date ASC;
    """
    move_avg_query = """
    SELECT seproject.historicaldata.Date, seproject.historicaldata.`{__value_name__}`, avg(historicaldata_past.`{__value_name__}`) as `{__value_name__}_window`
    FROM seproject.historicaldata
    JOIN (
        SELECT
        seproject.historicaldata.Date, seproject.historicaldata.`{__value_name__}`
        FROM seproject.historicaldata
        WHERE seproject.historicaldata.sym = '{__stockname__}'
    ) AS historicaldata_past 
      ON seproject.historicaldata.Date BETWEEN  historicaldata_past.Date and date_add(historicaldata_past.Date, interval + {__window__} day)
    WHERE seproject.historicaldata.sym = '{__stockname__}'
    GROUP BY 1, 2
    order by seproject.historicaldata.Date ASC;

    """
    rt_price = """
    SELECT price 
    FROM seproject.realtimedata
    WHERE sym = '{__stockname__}'
    """
    #rt_price1 = {}

    pred_price = round(analyzeSymbol(stockname),2)


    q_results = db.engine.execute(rt_price.format(__stockname__=stockname))
    #d = json.dumps(q_results)
    for res in q_results:
        chart_data = res[0]
    rt_price1= chart_data
    print(type(pred_price))    

    print(type(rt_price1))
    rec_BS_A = ['BUY','SELL']

    if float(rt_price1) < pred_price:
        rec_BS = rec_BS_A[0]
    else:
        rec_BS = rec_BS_A[1]


    chart_data_all = {}
    chart_data_all_sec = {}
    chart_data_all_th = {}

    for data_type in data_types:
        q_results = db.engine.execute(recent_trend_query.format(__stockname__=stockname, __value_name__=data_type))
        chart_values = []
        for result in q_results:
            unixtime = time.mktime(result[0].timetuple()) * 1000
            chart_values.append([unixtime, result[1]])
        chart_data_all[data_type] = chart_values

        q_results = db.engine.execute(move_avg_query.format(__stockname__=stockname, __value_name__=data_type, __window__=window))
        chart_values = []
        for result in q_results:
            unixtime = time.mktime(result[0].timetuple()) * 1000
            chart_values.append([unixtime, result[2]])
        chart_data_all_sec[data_type] = chart_values
        q_results = db.engine.execute(move_avg_query.format(__stockname__=stockname, __value_name__=data_type, __window__=window2))
        chart_values = []
        for result in q_results:
            unixtime = time.mktime(result[0].timetuple()) * 1000
            chart_values.append([unixtime, result[2]])
        chart_data_all_th[data_type] = chart_values
   
    return render_template("stockselect.html", chart_title=stockname, chart_data_all=chart_data_all, chart_data_all_sec=chart_data_all_sec,chart_data_all_th=chart_data_all_th, data_types=data_types, window=window, window2= window2,  rt_price= rt_price1, pred_price = pred_price, rec_BS = rec_BS, stock=stockname)


@app.route('/figure.png/<variable>')
def figure(chartID = 'chart_ID', chart_type = 'bar', chart_height = 350):
    chart = {"renderTo": chartID, "type": chart_type, "height": chart_height,}
    series = [{"name": 'Label1', "data": [1,2,3]}, {"name": 'Label2', "data": [4, 5, 6]}]
    title = {"text": 'My Title'}
    xAxis = {"categories": ['xAxis Data1', 'xAxis Data2', 'xAxis Data3']}
    yAxis = {"title": {"text": 'yAxis Label'}}
    return render_template('stockselect.html', chart_title=chart_title)  #, chartID=chartID, chart=chart, series=series, title=title, xAxis=xAxis, yAxis=yAxis)


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    resp = make_response(redirect('http://127.0.0.1:5000/home'))
    resp.set_cookie('login', expires=0)
    return resp


@app.route('/', methods=['POST', 'GET'])
def default():
    return redirect('http://127.0.0.1:5000/home')


# resource-server-side:
@app.route('/logined', methods=['POST', 'GET'])
def logined():
    token = request.args.get('token')
    ret = verify_token(token)
    if ret:
        return redirect('http://127.0.0.1:5000/home')
    else:
        resp = make_response(redirect('http://127.0.0.1:5000/home'))
        resp.set_cookie('login', expires=0)
        return redirect('http://127.0.0.1:5000/home')


@app.route('/FAQ', methods=['POST', 'GET'])
def faq():
    return render_template('FAQ.html')


@app.route('/myprofile', methods=['POST', 'GET'])
def myprofile():
    username = request.cookies.get('login').split('_')[0]
    # focused_stock = cursor.execute('SELECT favorite_stock FROM login_info WHERE user_name=%s', username)
    result = cursor.execute('SELECT favorite_stock FROM login_info WHERE user_name=%s', username)
    cnx.commit()
    return render_template('myprofile.html', stock=focused_stock)


@app.route('/addfav', methods=['POST', 'GET'])
def addfav():
    if request.method == 'POST':
        # data = request.get_json()
        # stock = data['stock_sent']
        stock = request.form['stock']
        username = request.cookies.get('login').split('_')[0]
        # password = request.cookies.get('login').split('_')[1]
        # email = request.cookies.get('login').split('_')[2]

        cursor.execute('UPDATE login_info SET favorite_stock=%s WHERE user_name=%s', (stock, username))
        # cursor.execute('INSERT INTO login_info VALUES(%s,%s,%s,%s)', (username, password, email, stock))
        cnx.commit()
        uri = 'http://127.0.0.1:5000/stock?username=%s&stock_name=%s' % (username, stock)
        return redirect(uri)


@app.route('/defav', methods=['POST', 'GET'])
def defav():
    if request.method == 'POST':
        stock = request.form['stock']
        username = request.cookies.get('login').split('_')[0]
        cursor.execute('UPDATE login_info SET favorite_stock=%s WHERE user_name=%s', ('', username))
        cnx.commit()
        uri = 'http://127.0.0.1:5000/stock?username=%s&stock_name=%s' % (username, stock)
        return redirect(uri)


if __name__ == '__main__':
    app.run(debug=True)
