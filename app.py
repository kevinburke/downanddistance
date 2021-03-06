import os
import pprint

from bs4 import BeautifulSoup
from flask import Flask, render_template, request, flash, redirect
import requests

app = Flask(__name__)
app.secret_key = (os.environ.get('DD_FLASK_SECRET', None) or
                  'eK+sm^.2E{yBE26taB]cfCGDgCXjqEsequtRBTLD')

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
        params['ydline'] = 100 - yard_line
    else:
        params['fldside'] = 'opp'
        params['ydline'] = yard_line
    params['scorediff'] = args.get('margin', '', int)
    params['qtr'] = args.get('quarter', '', int)
    params['minleft'] = args.get('minutes', '', int)
    params['sec'] = args.get('seconds', '', int)
    return params

def parse_stats(html):
    """ Please, don't look too hard at this. """

    soup = BeautifulSoup(html)
    table = soup.find('table')
    rows = table.findAll('tr')
    first_pass_be = first_pass_sr = True
    d = {
        'go_for_it':  {'action': 'go_for_it',
                       'friendly_name': 'go for it'},
        'punt':       {'action': 'punt',
                       'friendly_name': 'punt',},
        'field_goal': {'action': 'field_goal',
                       'friendly_name': 'field goal'}
    }

    for row in rows:
        if row.get('id', None):
            continue
        cols = row.findAll('td')

        if cols[0].text == 'Break-Even:':
            row_title = ('expected_break_even' if first_pass_be
                         else 'win_break_even')
            first_pass_be = not first_pass_be
            print row_title

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
    diff = item2['expected_points_total'] - item1['expected_points_total']
    return cmp(diff, 0)

def compare_wp(item1, item2):
    diff = item2['win_probability_total'] - item1['win_probability_total']
    return cmp(diff, 0)

@app.route('/calc')
def calculate():
    # validate parameters
    for param in ['to_go', 'field_position']:
        if request.args.get(param, type=int) is None:
            flash("Please provide a valid number for {}".format(param))
            return redirect('/')

    # fetch the data
    params = get_stat_params(request.args)
    r = requests.get('http://wp.advancednflstats.com/4thDownCalc.php',
                     params=params,
                     headers={'User-Agent': 'DownAndDistance/1.0'})
    d = parse_stats(r.content)

    # fancy logic!
    # first check if the win probability and expected probability agree about
    # what to do
    go = d['go_for_it']
    punt = d['punt']
    fg = d['field_goal']

    ep_sorted = sorted([go, punt, fg], cmp=compare_ep)
    wp_sorted = sorted([go, punt, fg], cmp=compare_wp)

    if ep_sorted[0] != wp_sorted[0] and params['scorediff']:
        same = False
        winner_ep = ep_sorted[0]['friendly_name']
        winner_wp = wp_sorted[0]['friendly_name']
    else:
        same = True
        winner_ep = winner_wp = ep_sorted[0]['friendly_name']

    show_field_goal = d['field_goal']['expected_success_rate'] > 0.01

    return render_template(
        'calc.html', same=same, winner_ep=winner_ep, winner_wp=winner_wp,
        to_go=request.args.get('to_go'), field_position=params['ydline'], d=d,
        show_field_goal=show_field_goal)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
