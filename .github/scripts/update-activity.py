import html
import json
import os
from pathlib import Path
import re
import subprocess

START = '<!-- ACTIVITY:START -->'
END = '<!-- ACTIVITY:END -->'


def update_readme(readme, pulls, owner):
    if readme.count(START) != 1 or readme.count(END) != 1:
        raise ValueError('README must contain exactly one activity block.')
    before, _, remaining = readme.partition(START)
    _, _, after = remaining.partition(END)
    if END in before:
        raise ValueError('Activity markers are in the wrong order.')

    entries = []
    seen = set()
    for pull in pulls:
        repository = pull['repository']['nameWithOwner']
        if repository.split('/')[0].lower() == owner.lower():
            continue
        key = (repository, pull['title'])
        if key in seen:
            continue
        seen.add(key)
        title = html.escape(' '.join(pull['title'].split()), quote=False)
        title = re.sub(r'([\\`*_\[\]])', r'\\\1', title)
        entries.append(f"- [{title}]({pull['url']}) in [{repository}](https://github.com/{repository})")
        if len(entries) == 5:
            break

    activity = '\n'.join(entries) or 'No public merged contributions yet.'
    return f'{before}{START}\n{activity}\n{END}{after}'


if __name__ == '__main__':
    owner = os.environ['GITHUB_REPOSITORY_OWNER']
    result = subprocess.run(
        ['gh', 'search', 'prs', '--author', owner, '--merged', '--visibility',
         'public', '--sort', 'updated', '--limit', '30', '--json',
         'repository,title,url'],
        check=True, capture_output=True, text=True,
    )
    path = Path('README.md')
    original = path.read_text(encoding='utf-8')
    updated = update_readme(original, json.loads(result.stdout), owner)
    if updated != original:
        path.write_text(updated, encoding='utf-8')
