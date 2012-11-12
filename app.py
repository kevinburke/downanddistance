import os
import pprint

from bs4 import BeautifulSoup
from flask import (Flask, render_template, request, flash, redirect,
    make_response)
import requests

app = Flask(__name__)
app.secret_key = 'eK+sm^.2E{yBE26taB]cfCGDgCXjqEsequtRBTLD'

my_titles = {
    'EP Fail: ': 'expected_points_failure',
    'EP Success': 'expected_points_success',
    'EP Total: ': 'expected_points_total',
    'Success Rate: ': 'success_rate',
    'WP Fail: ': 'win_probability_failure',
    'WP Success': 'win_probability_success',
    'WP Total: ': 'win_probability_total',
}

def get_stat_params(args):
    """ Return a dictionary of Advanced NFL Stat params based on mine """

    params = {}
    params['togo'] = args.get('to_go', type=int)
    yard_line = args.get('field_position', type=int)
    if yard_line > 50:
        params['fldside'] = 'own'
        params['ydline'] = yard_line - 50
    else:
        params['fldside'] = 'opp'
        params['ydline'] = yard_line
    params['scorediff'] = args.get('margin', type=int)
    params['qtr'] = args.get('quarter', type=int)
    params['minleft'] = args.get('minutes', type=int)
    params['sec'] = args.get('seconds', type=int)
    return params

def parse_stats(html):
    """ Please, don't look too hard at this. """

    soup = BeautifulSoup(html)
    table = soup.find('table')
    rows = table.findAll('tr')
    first_pass_be = first_pass_sr = False
    d = {
        'go_for_it':  {'action': 'go_for_it'},
        'punt':       {'action': 'punt'},
        'field_goal': {'action': 'field_goal'}
    }

    for row in rows:
        if row.get('id', None):
            continue
        cols = row.findAll('td')

        if cols[0].text == 'Break-Even:':
            row_title = ('expected_break_even' if first_pass_be
                         else 'win_break_even')
            first_pass_be = not first_pass_be

        elif cols[0].text == 'Success Rate: ':
            row_title = ('expected_success_rate' if first_pass_sr
                         else 'win_success_rate')
            first_pass_sr = not first_pass_sr

        else:
            row_title = my_titles[cols[0].text]

        for i, action in enumerate(['go_for_it', 'punt', 'field_goal']):
            try:
                d[action][row_title] = float(cols[i + 1].text)
            except ValueError:
                # the td doesn't contain a number, ignore
                pass

    return d

@app.route('/')
def home():
    return render_template('index.html')

def compare_ep(item1, item2):
    return item1['expected_points_total'] > item2['expected_points_total']

def compare_wp(item1, item2):
    return item1['win_probability_total'] > item2['win_probability_total']

@app.route('/calc')
def calculate():
    # validate parameters
    for param in ['to_go', 'field_position', 'margin', 'quarter', 'minutes',
                  'seconds']:
        if request.args.get(param, type=int) is None:
            flash("Please provide a valid number for {}".format(param))
            return redirect('/')


    # fetch the data
    params = get_stat_params(request.args)
    r = requests.get('http://wp.advancednflstats.com/4thDownCalc.php',
                     params=params)
    d = parse_stats(r.content)

    # fancy logic!
    # first check if the win probability and expected probability agree about
    # what to do
    go = d['go_for_it']
    punt = d['punt']
    fg = d['field_goal']

    ep_sorted = sorted([go, punt, fg], cmp=compare_ep)
    wp_sorted = sorted([go, punt, fg], cmp=compare_wp)

    if ep_sorted[0] == wp_sorted[0]:
        same = True
        winner_ep = winner_wp = ep_sorted[0]['action']
    else:
        same = False
        winner_ep = ep_sorted[0]['action']
        winner_wp = wp_sorted[0]['action']

    # render some html.
    return render_template('calc.html', same=same, winner_ep=winner_ep,
                           winner_wp=winner_wp, d=d)

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 5000.
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
