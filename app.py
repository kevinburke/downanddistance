import os

from flask import Flask, render_template, request, flash, redirect
import requests

app = Flask(__name__)
app.secret_key = 'eK+sm^.2E{yBE26taB]cfCGDgCXjqEsequtRBTLD'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/calc')
def calculate():
    for param in ['to_go', 'field_position', 'margin', 'quarter', 'minutes',
                  'seconds']:
        try:
            arg = request.args.get(param, type=int)
            if arg is None:
                flash("Please provide a valid number for {}".format(param))
                return redirect('/')
        except Exception:
            pass
    return 'hi'

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
