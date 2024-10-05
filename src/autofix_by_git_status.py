import argparse
import json
import os
import subprocess

from src import review

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--CONFIG', type=str, help='Config')
    parser.add_argument('--PROJECT_PATH', type=str, help='Project path')

    args = parser.parse_args()

    with open(args.CONFIG, 'r') as data:
        config = json.load(data)

    regex_order = config['regexOrder']
    project_path = args.PROJECT_PATH

    git_status_output = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=project_path,
        stdout=subprocess.PIPE,
        text=True
    ).stdout

    for obj in git_status_output.split("\n"):
        obj = obj.split(" ")

        for remove in ["", "M"]:
            if remove in obj:
                obj.remove(remove)

        if len(obj) != 1:
            continue

        file = obj[0]

        if not file.endswith(('.cpp', '.h', '.hpp', '.h')):
            continue

        path = os.path.join(project_path, file)
        _, _, new_data = review.verify(path=path, regex_order=regex_order)

        with open(path, "w") as data:
            data.writelines(new_data)
