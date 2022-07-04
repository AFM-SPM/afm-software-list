from functools import lru_cache
import json
import pathlib
import sys
from urllib.parse import urlparse

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
        if name == "Operating System":
            # Special confirmation questions for operating systems
            value = []
            for ops in ["Windows", "macOS", "Linux"]:
                sup = click.confirm(
                    "Does this software support {}?".format(ops))
                if sup:
                    value.append(ops)
        else:
            # Standard prompt
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
        json.dump(data, fd, indent=2)
    generate_issue_template()
    recreate_json_entries()


@click.command()
def check_entries():
    """Perform sanity checks for all list entries"""
    with KEYWORD_FILE.open() as fd:
        kwdata = json.load(fd)
    click.secho("Checking entries...", bold=True)
    warnings = []
    errors = []
    files = sorted(ENTRY_DIR.glob("*.json"))
    for path in files:
        print(f"Checking {path.name}...")
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


@click.command()
def run_maintenance():
    """Run automated maintenance tasks"""
    generate_issue_template()
    recreate_json_entries()


@click.command()
@click.option("-o", "--output-dir")
def export_list(output_dir):
    """Generate the software list from all entries"""
    # This directory is not under version control.
    # It is renamed to "docs" and served via the gh-pages branch
    # (This process is automated using GitHub Actions).
    dout = pathlib.Path(output_dir)
    dout.mkdir(exist_ok=True)
    # create .csv list
    export_to_csv(dout / "afm-software.csv", delimiter=", ")
    # create .tsv list
    export_to_csv(dout / "afm-software.tsv", delimiter="\t")
    # create .html list
    export_to_html(dout / "afm-software.html", icons=False)
    # create .html list with icons
    export_to_html(dout / "afm-software-wicons.html", icons=True)
    # create .html list with icons for jekyll
    export_to_html(dout / "afm-software-wicons-jekyll.html", icons=True,
                   jekyll=True)


def export_to_csv(path, delimiter=", "):
    # parameters
    header = [item["name"] for item in json.load(KEYWORD_FILE.open())]
    entries = [json.load(pp.open()) for pp in sorted(ENTRY_DIR.glob("*.json"))]
    with path.open("w") as fd:
        # header
        fd.write(delimiter.join(header) + "\r\n")
        # entries
        for ent in entries:
            values = []
            for key in header:
                value = ent[key]
                if value is None:
                    value = ""
                elif isinstance(value, list):
                    value = " ".join(value)
                values.append(value)
            fd.write(delimiter.join(values) + "\r\n")


def export_to_html(path, table_id="afmlist-table", tr_class="afmlist-header",
                   icons=False, jekyll=False):
    # parameters
    header = [item["name"] for item in json.load(KEYWORD_FILE.open())]
    entries = [json.load(pp.open()) for pp in sorted(ENTRY_DIR.glob("*.json"))]
    with KEYWORD_FILE.open() as fd:
        kwdata = json.load(fd)
    lines = []
    lines.append('<table id="{}">'.format(table_id))
    # header
    lines.append('<tr class="{}">'.format(tr_class))
    for hh in header:
        if icons:
            if hh == "Homepage":
                hicon = "🏡"
            elif hh == "Repository":
                hicon = "🖧"
            elif hh == "Download Page":
                hicon = "⏬"
            elif hh == "Documentation":
                hicon = "👓"
            elif hh == "Operating System":
                hicon = "OS"
            else:
                hicon = hh
            hh = '<span title="{}">{}</span>'.format(hh, hicon)
        lines.append("<th> {} </th>".format(hh))
    lines.append('</tr>')
    # entries
    for ent in entries:
        lines.append("<tr>")
        for item in kwdata:
            name = item["name"]
            dtype = item["type"]
            value = ent[name]
            if value is None:
                value = ""
            elif isinstance(value, list):
                value = " ".join(value)
                if icons:
                    if name == "Operating System":
                        value = value.replace("macOS",
                                              '<span title="macOS">⌘</span>')
                        value = value.replace("Windows",
                                              '<span title="Windows">❖</span>')
                        value = value.replace("Linux",
                                              '<span title="Linux">🐧</span>')

            elif dtype == "url":
                if icons:
                    favicon = download_favicon(value, path.parent / "favicons")
                    if favicon is None:
                        icon = "🌐"
                    else:
                        ip = favicon.relative_to(path.parent)
                        if jekyll:
                            # Since with jekyll, the file is included at
                            # the top level, we have to prepend "static".
                            ip = "static/{}".format(ip)
                        icon = '<img src="{}" style="height:1em;">'.format(ip)
                else:
                    icon = value
                value = '<a href="{}" title="{} of {}">{}</a>'.format(
                    value, name, ent["Name"], icon)
            lines.append("<td> {} </td>".format(value))
        lines.append("</tr>")
    lines.append('</table>')
    path.write_text("\r\n".join(lines))


@lru_cache(maxsize=500)
def download_favicon(url, download_dir):
    """Extract the domain from a URL and store the favicon on disk"""
    download_dir = pathlib.Path(download_dir)
    download_dir.mkdir(parents=True, exist_ok=True)
    # get URL
    parsed_uri = urlparse(url)
    domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
    # get favicon
    resp = requests.get(domain + "/favicon.ico")
    if resp.status_code == 200:
        path = download_dir / (parsed_uri.netloc + ".ico")
        with path.open("wb") as fd:
            fd.write(resp.content)
        return path
    else:
        return None


def generate_issue_template():
    """Generate the GitHub issue template for new software entries"""
    tdir = pathlib.Path(__file__).parent / ".github" / "ISSUE_TEMPLATE"
    tpath = tdir / "new-software-list-entry.md"
    lines = tpath.read_text().split("\n")[:11]
    lines.append("```json")
    # Add template
    with KEYWORD_FILE.open() as fd:
        data = json.load(fd)
    template = {}
    for item in data:
        template[item["name"]] = None
    dumped = json.dumps(template, indent=2)
    [lines.append(dd) for dd in dumped.split("\n")]
    lines.append("```")
    tpath.write_text("\n".join(lines))


def recreate_json_entries():
    """Rcreate all json entries

    This is used for fixing manual formatting errors or when new
    keys are added.
    """
    with KEYWORD_FILE.open() as fd:
        data = json.load(fd)
    for path in ENTRY_DIR.glob("*.json"):
        with path.open() as fd:
            entry = json.load(fd)
        # insert new columns
        for item in data:
            name = item["name"]
            if name not in entry:
                entry[name] = None
            if name == "Operating System" and entry[name]:
                entry[name] = sorted(entry[name])
        # save entry
        with path.open("w") as fd:
            json.dump(entry, fd, sort_keys=True, indent=2, ensure_ascii=False)


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
cli.add_command(export_list)
cli.add_command(run_maintenance)


if __name__ == "__main__":
    cli()
