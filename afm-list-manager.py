import json
import pathlib
import sys

import click
import requests
from slugify import slugify


@click.group()
def cli():
    pass


@click.command()
def add_entry():
    """Add a new entry to the software list"""
    with KEYWORD_FILE.open() as fd:
        data = json.load(fd)
    entry = {}
    for item in data:
        name = item["name"]
        dtype = item["type"]
        promptkwds = {
            "text": name,
            "default": "",
            "type": KEYWORD_TYPES[dtype]}
        value = click.prompt(**promptkwds)
        if value == "":
            value = None
        entry[name] = value
    # save the entry
    fname = slugify(entry["Name"]) + ".json"
    path = ENTRY_DIR / fname
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
    with KEYWORD_FILE.open() as fd:
        data = json.load(fd)
    data.append({"name": name,
                 "type": dtype})
    with KEYWORD_FILE.open("w") as fd:
        json.dump(sorted(data, key=lambda x: x["name"]), fd, indent=2)


@click.command()
def check_entries():
    """Perform sanity checks for all list entries"""
    with KEYWORD_FILE.open() as fd:
        kwdata = json.load(fd)
    click.secho("Checking entries...", bold=True)
    warnings = []
    errors = []
    with click.progressbar(sorted(ENTRY_DIR.glob("*.json"))) as bar:
        for path in bar:
            with path.open() as fd:
                data = json.load(fd)
            for item in kwdata:
                name = item["name"]
                if item["type"] == "url" and data[name] is not None:
                    try:
                        valid = verify_url(data[name])
                    except BaseException:
                        valid = False
                    if not valid:
                        errors.append("URL broken for '{}': '{}' ({})".format(
                            path.name, item["name"], data[name]))
    for err in errors:
        click.secho(err, bold=True, fg="red", err=True)

    if errors:
        click.secho("There were errors.", bold=True, fg="red")
        sys.exit(1)

    if warnings:
        click.secho("There were warnings.", bold=True, fg="yellow")
        sys.exit(2)

    click.secho("Success.", bold=True, fg="green")


def generate_issue_template():
    """Generate the GitHub issue template for new software entries"""
    pass


def verify_url(url):
    """Verify that a URL is valid"""
    request = requests.get(url)
    return request.status_code == 200


ENTRY_DIR = pathlib.Path(__file__).parent / "entries"

KEYWORD_FILE = pathlib.Path(__file__).parent / "entry_keywords.json"

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
cli.add_command(check_entries)


if __name__ == "__main__":
    cli()
