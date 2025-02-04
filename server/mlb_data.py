"""
MIT License

Copyright (c) 2024 [Xinpeng Shou]

See LICENSE file for the complete license terms.
"""

import requests
import json


def get_current_play_info(game_id):
    url = f"https://statsapi.mlb.com/api/v1.1/game/716463/feed/live"

    try:
        response = requests.get(url)
        data = response.json()
        all_plays = data['liveData']['plays']['allPlays']

        play_info_list = []
        for current_play in all_plays:
            play_info = {
                'result': {
                    'type': current_play['result']['type'],
                    'event': current_play['result']['event'],
                    'eventType': current_play['result']['eventType'],
                    'description': current_play['result']['description'],
                    'rbi': current_play['result']['rbi'],
                    'awayScore': current_play['result']['awayScore'],
                    'homeScore': current_play['result']['homeScore'],
                    'isOut': current_play['result']['isOut']
                },
                'about': {
                    "atBatIndex": current_play['about']['atBatIndex'],
                    "halfInning": current_play['about']['halfInning'],
                    "isTopInning": current_play['about']['isTopInning'],
                    "inning": current_play['about']['inning'],
                    "startTime": current_play['about']['startTime'],
                    "endTime": current_play['about']['endTime'],
                    "isComplete": current_play['about']['isComplete'],
                    "isScoringPlay": current_play['about']['isScoringPlay'],
                },
                'count': {
                    'balls': current_play['count']['balls'],
                    'strikes': current_play['count']['strikes'],
                    'outs': current_play['count']['outs']
                },
                'runners': [{
                    'movement': {
                        'originBase': runner['movement'].get('originBase'),
                        'start': runner['movement'].get('start'),
                        'end': runner['movement'].get('end'),
                        'outBase': runner['movement'].get('outBase'),
                        'isOut': runner['movement'].get('isOut'),
                        'outNumber': runner['movement'].get('outNumber')
                    },
                    'details': {
                        'event': runner['details'].get('event'),
                        'eventType': runner['details'].get('eventType'),
                        'movementReason': runner['details'].get('movementReason'),
                        'runner': {
                            'id': runner['details'].get('runner', {}).get('id'),
                            'fullName': runner['details'].get('runner', {}).get('fullName'),
                            'link': runner['details'].get('runner', {}).get('link')
                        },
                        'responsiblePitcher': runner['details'].get('responsiblePitcher'),
                        'isScoringEvent': runner['details'].get('isScoringEvent'),
                        'rbi': runner['details'].get('rbi'),
                        'earned': runner['details'].get('earned'),
                        'teamUnearned': runner['details'].get('teamUnearned'),
                        'playIndex': runner['details'].get('playIndex')
                    },
                    'credits': [{
                        'player': {
                            'id': credit.get('player', {}).get('id'),
                            'link': credit.get('player', {}).get('link')
                        },
                        'position': {
                            'code': credit.get('position', {}).get('code'),
                            'name': credit.get('position', {}).get('name'),
                            'type': credit.get('position', {}).get('type'),
                            'abbreviation': credit.get('position', {}).get('abbreviation')
                        },
                        'credit': credit.get('credit')
                    } for credit in runner.get('credits', [])]
                } for runner in current_play.get('runners', [])],
                'pitchIndex': current_play.get('pitchIndex', []),
                'actionIndex': current_play.get('actionIndex', [])
            }
            play_info_list.append(play_info)

        return play_info_list

    except Exception as e:
        print(f"Error: {e}")
        return None


def print_play_info(play_info_list):
    if not play_info_list:
        return

    for i, play_info in enumerate(play_info_list, 1):
        print(f"\n=== Play {i} ===")
        print("\nResult:")
        print(f"type: \"{play_info['result']['type']}\"")
        print(f"event: \"{play_info['result']['event']}\"")
        print(f"eventType: \"{play_info['result']['eventType']}\"")
        print(f"description: \"{play_info['result']['description']}\"")
        print(f"rbi: {play_info['result']['rbi']}")
        print(f"awayScore: {play_info['result']['awayScore']}")
        print(f"homeScore: {play_info['result']['homeScore']}")
        print(f"isOut: {play_info['result']['isOut']}")

        print("\nCount:")
        print(f"balls: {play_info['count']['balls']}")
        print(f"strikes: {play_info['count']['strikes']}")
        print(f"outs: {play_info['count']['outs']}")

        print("\nAbout:")
        print(f"atBatIndex: {play_info['about']['atBatIndex']}")
        print(f"halfInning: {play_info['about']['halfInning']}")
        print(f"isTopInning: {play_info['about']['isTopInning']}")
        print(f"inning: {play_info['about']['inning']}")
        print(f"startTime: {play_info['about']['startTime']}")
        print(f"endTime: {play_info['about']['endTime']}")
        print(f"isComplete: {play_info['about']['isComplete']}")
        print(f"isScoringPlay: {play_info['about']['isScoringPlay']}")

        print("\nRunners:")
        for j, runner in enumerate(play_info['runners'], 1):
            print(f"\nRunner {j}:")
            print("Movement:")
            movement = runner['movement']
            print(f"originBase: {movement['originBase']}")
            print(f"start: {movement['start']}")
            print(f"end: \"{movement['end']}\"")
            print(f"outBase: {movement['outBase']}")
            print(f"isOut: {movement['isOut']}")
            print(f"outNumber: {movement['outNumber']}")

            print("\nDetails:")
            details = runner['details']
            print(f"event: \"{details['event']}\"")
            print(f"eventType: \"{details['eventType']}\"")
            print(f"movementReason: {details['movementReason']}")
            print("Runner:")
            runner_details = details['runner']
            print(f"id: {runner_details['id']}")
            print(f"fullName: \"{runner_details['fullName']}\"")
            print(f"link: \"{runner_details['link']}\"")
            print(f"responsiblePitcher: {details['responsiblePitcher']}")
            print(f"isScoringEvent: {details['isScoringEvent']}")
            print(f"rbi: {details['rbi']}")
            print(f"earned: {details['earned']}")
            print(f"teamUnearned: {details['teamUnearned']}")
            print(f"playIndex: {details['playIndex']}")

            print("\nCredits:")
            for credit in runner['credits']:
                print("Player:")
                print(f"id: {credit['player']['id']}")
                print(f"link: \"{credit['player']['link']}\"")
                print("Position:")
                print(f"code: \"{credit['position']['code']}\"")
                print(f"name: \"{credit['position']['name']}\"")
                print(f"type: \"{credit['position']['type']}\"")
                print(f"abbreviation: \"{credit['position']['abbreviation']}\"")
                print(f"credit: \"{credit['credit']}\"")

        print("\nIndexes:")
        print(f"pitchIndex: {play_info['pitchIndex']}")
        print(f"actionIndex: {play_info['actionIndex']}")


def save_live_data(play_info_list):
    if play_info_list:
        data = {
            'liveData': {
                'plays': {
                    'allPlays': play_info_list
                }
            }
        }

        with open('liveData.json', 'w') as f:
            json.dump(data, f, indent=2)


if __name__ == "__main__":
    game_id = "716463"
    play_info_list = get_current_play_info(game_id)
    save_live_data(play_info_list)  # Save the data to JSON file
    print_play_info(play_info_list)  # Print the data for debugging
