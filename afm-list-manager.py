import json
import pathlib

import click
import requests
from slugify import slugify


@click.group()
def cli():
    pass


@click.command()
def add_entry():
    """Add a new entry to the software list"""
    with open(KEYWORD_FILE) as fd:
        data = json.load(fd)
    entry = {}
    for item in data:
        name = item["name"]
        dtype = item["type"]
        promptkwds = {"text": name, "default": ""}
        if item["type"] in KEYWORD_VALIDATORS:
            promptkwds["value_proc"] = KEYWORD_VALIDATORS[dtype]
        else:
            promptkwds["type"] = KEYWORD_TYPES[dtype]
        value = click.prompt(**promptkwds)
        if value == "":
            value = None
        entry[name] = value
    # save the entry
    fname = slugify(entry["Name"]) + ".json"
    path = pathlib.Path(__file__).parent / "entries" / fname
    if path.exists():
        raise ValueError("Entry already exists: {}".format(fname))
    with path.open("w") as fd:
        json.dump(entry, fd, sort_keys=True, indent=2, ensure_ascii=False)


@click.command()
def add_keyword():
    """Add a new keyword entry"""
    name = click.prompt('Please enter the keyword name', type=str)
    dtype = click.prompt(text='Please enter the data type',
                         default="str",
                         type=click.Choice(sorted(KEYWORD_TYPES.keys())))
    with open(KEYWORD_FILE) as fd:
        data = json.load(fd)
    data.append({"name": name,
                 "type": dtype})
    with open(KEYWORD_FILE, "w") as fd:
        json.dump(sorted(data, key=lambda x: x["name"]), fd, indent=2)


def generate_issue_template():
    """Generate the GitHub issue template for new software entries"""
    pass


def verify_url(url):
    """Verify that a URL is valid"""
    request = requests.get(url)
    return request.status_code == 200


KEYWORD_FILE = "entry_keywords.json"

KEYWORD_TYPES = {
    "float": float,
    "int": int,
    "list": list,
    "str": str,
    "url": str,
}

KEYWORD_VALIDATORS = {
    "url": verify_url,
    "list": lambda x: [f.strip() for f in x.split()]
}

cli.add_command(add_entry)
cli.add_command(add_keyword)


if __name__ == "__main__":
    cli()
