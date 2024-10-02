import argparse
import json

import review

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--PATH', type=str, help='Path')
    parser.add_argument('--CONFIG', type=str, help='Config')

    args = parser.parse_args()

    with open(args.CONFIG, 'r') as data:
        config = json.load(data)

    path = args.PATH
    regex_order = config['regexOrder']

    if not path.endswith(".h") and not path.endswith(".cpp"):
        raise Exception("extension type not supported")

    changed, _, new_data = review.verify(path=path, regex_order=regex_order)

    if changed:
        with open(path, "w") as data:
            data.writelines(new_data)
