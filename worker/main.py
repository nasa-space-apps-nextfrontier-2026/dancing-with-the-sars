import argparse
import json

from backend.app.agents import NAMES, unavailable


def run_once() -> dict:
    return {'synthetic': True, 'status': 'unavailable', 'results': [unavailable(x).__dict__ for x in NAMES]}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CIVISAR no-network synthetic worker scaffold')
    parser.add_argument('--once', action='store_true', required=True)
    parser.parse_args()
    print(json.dumps(run_once(), default=str))
