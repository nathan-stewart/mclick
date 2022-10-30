
from flask import Flask, render_template, request


app = Flask(__name__)
@app.route('/', methods = ['GET', 'PUT'])
def index():
    header = 'MClick!'
    print(request.form.get('sliderTempo'))
    return render_template('index.html', header=header)
