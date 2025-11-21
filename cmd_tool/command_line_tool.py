import argparse

import requests

from git import Repo

import os


def get_file_from_github(path, branch="main"):
    repo = Repo(os.path.dirname(os.path.abspath(__file__)))
    file_content = repo.git.show("HEAD:{path}".format(path=path))
    return file_content


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Process some command-line arguments.")

    parser.add_argument("--path", type=str, help="Path to the file containing" \
    " the file name in the repository")
    
    arguments = parser.parse_args()

    path = arguments.path

    content = get_file_from_github(path)
    print(content)
