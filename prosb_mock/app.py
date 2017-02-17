from flask import Flask, jsonify, make_response, request

from data import dataset_players, dataset_squads, dataset_matches, dataset_matches_details

app = Flask(__name__)


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.route('/api/player-gameaccounts')
def get_account():
    gamePlatform = request.args.get('gamePlatform', '')
    account = request.args.get('account', '')
    player_ = [player for player in dataset_players if
               player.get('gamePlatform', {}).get('key') == gamePlatform and player.get('account') == account]
    return jsonify(player_)


@app.route('/api/team-squads')
def get_squads():
    gamePlatform = request.args.get('gamePlatform', '')
    players = request.args.get('players', '').split(',')
    squads = [squad for squad in dataset_squads if
              squad.get('gamePlatform', {}).get('key') == gamePlatform and set(players) == set(squad.get('players'))]
    return jsonify(squads)


@app.route('/api/matches')
def get_matches():
    status = request.args.get('status', '').split(',')
    squads_keys = set(request.args.get('squads', '').split(','))
    sort = request.args.get('sort', '')
    match_ = [match for match in dataset_matches if
              match.get('matchStatus') in status and squads_keys.issubset(match.get('squads'))]
    return jsonify(sorted(match_, key=lambda m: m.get(sort)))


@app.route('/api/matches/<string:key>/detail')
def get_matches_info(key):
    match_info = next(match_detail for match_detail in dataset_matches_details if
                      match_detail.get('match', {}).get('key') == key)
    return jsonify(match_info)


if __name__ == '__main__':
    app.run(debug=True)
