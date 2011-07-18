# -*- coding:utf-8 -*-

import os
import hashlib
from flask import Flask
from flask import render_template
from flask import redirect
from flask import request

app = Flask(__name__)
SALT = ''


def md5(string):
    return hashlib.md5(string).hexdigest()

@app.route('/')
def index():
    try:
        import config
    except ImportError as e:
        return redirect('/install')

    return render_template('index.jinja2')

@app.route('/install', methods=['GET', 'POST'])
def install():
    try:
        import config
        return redirect('/')
    except ImportError as e:
        if request.method == 'POST':
            host = request.form['host']
            email = request.form['user_email']
            password = request.form.get('user_password', '')

            f = open(os.path.join(os.path.dirname(__file__), 'config.py'), 'w')
            f.write('host = "%s"\n'%host)
            f.write('user_email = "%s"\n'%email)
            f.write('user_password = "%s"\n'%md5(password+SALT))
            f.close()
            return redirect('/')

        return render_template('install.jinja2')
    
    return redirect('/')

@app.route('/dojo', methods=['GET', 'POST'])
def dojo():
    try:
        import config
    except ImportError as e:
        return redirect('/install')

    if request.method == 'GET':
        return redirect('/')

    email = request.form['user_email']
    name = request.form['user_name']
    password = request.form.get('user_password', '')
    key = md5(email+SALT)

    if email and name:
        if config.user_email == email:
            if config.user_password == md5(password+SALT):
                return render_template('dojo.jinja2', 
                                       host=config.host, 
                                       user_email_hash=md5(email),
                                       key=key)
            else:
                return redirect('/')
        else:
            return render_template('dojo.jinja2', 
                                   host=config.host, 
                                   user_email_hash=md5(email),
                                   key=key)
    else:
        return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)