
from flask import Flask, render_template, request


app = Flask(__name__)

parameters = {
'tempo' : 120,
'measure_length' : 4,
'measure_volume' : 80,
'beat_volume': 80,
'eighth_volume' : 0,
'swing_value' : 0,
'sixteenth_volume' : 0
}

measures = ['2','3','4','6','9','12'] # yeah I left out 5 and 13 on purpose, showoff!

@app.route('/', methods = ['GET', 'POST' ])
def index():
    if (request.method == 'POST'):
        results = request.form.to_dict(flat=True)
        parameters['tempo'] =  int(results['tempo_slider'])
        parameters['measure_volume'] = int(results['measure_volume'])
        parameters['beat_volume'] = int(results['beat_volume'])
        parameters['eighth_volume'] = int(results['eighth_volume'])
        parameters['sixteenth_volume'] = int(results['sixteenth_volume'])
        parameters['swing_value'] = int(results['swing_value'])
        select_options = ''
        for i in measures:
            selected = ''
            if results['measure_length'] == i:
                selected = ' selected '
            select_options = select_options + '  <option value=%s%s>%s</option>' % (i, selected, i)
        parameters['measure_length'] = select_options
        print(parameters)
    return render_template('index.html', parameters=parameters)
