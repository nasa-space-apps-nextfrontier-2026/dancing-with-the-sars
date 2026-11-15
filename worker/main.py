import argparse
import json

from backend.app.agents import NAMES, unavailable


def run_once() -> dict:
    return {'synthetic': True, 'status': 'unavailable', 'results': [unavailable(x).__dict__ for x in NAMES]}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='CIVISAR worker: scaffold run or publish ML outputs')
    parser.add_argument('--once', action='store_true', help='no-network scaffold run')
    parser.add_argument('--publish', action='store_true', help='publish ML artifacts for the API')
    parser.add_argument('--damage', help='NISAR damage table (.parquet or .csv)')
    parser.add_argument('--history', help='Black Marble per-cell history (.csv.gz)')
    parser.add_argument('--fires', action='store_true', help='also fetch the live FIRMS feed')
    parser.add_argument('--agents', action='store_true',
                        help='publish the agents (ranking, insights, assistant, budget, buildings)')
    parser.add_argument('--table', default='data/local/building_table.parquet', help='U-04 building table')
    parser.add_argument('--out', default='data/published')
    args = parser.parse_args()
    if args.publish:
        from worker.publish import publish
        print(json.dumps(publish(args.out, args.damage, args.history, args.fires), default=str))
    elif args.agents:
        from worker.agents.publish_agents import publish_agents
        print(json.dumps(publish_agents(args.out, args.table), default=str))
    elif args.once:
        print(json.dumps(run_once(), default=str))
    else:
        parser.error('use --once, --publish or --agents')
