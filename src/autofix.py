import argparse
import json

import review


def autofix(path, config):
    regex_order = config['regexOrder']

    if not path.endswith(".h") and not path.endswith(".cpp"):
        raise Exception("extension type not supported")

    changed, _, new_data = review.verify(path=path, regex_order=regex_order)

    if changed:
        with open(path, "w") as data:
            data.writelines(new_data)

    return changed


def autofix_from_config(path, config_path):
    with open(config_path, 'r') as data:
        config = json.load(data)

    return autofix(path=path, config=config)


if __name__ == '__main__':  # pragma: no cover
    parser = argparse.ArgumentParser()
    parser.add_argument('--PATH', type=str, help='Path')
    parser.add_argument('--CONFIG', type=str, help='Config')

    args = parser.parse_args()

    autofix_from_config(path=args.PATH, config_path=args.CONFIG)
