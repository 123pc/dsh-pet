"""Collect bundled dependency notices and the exact GPL component source archive."""
from pathlib import Path
import json
import shutil
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
MODULES = ROOT / 'dsh-pet/node_modules'
LICENSES = ROOT / 'docs/licenses'
LICENSES.mkdir(parents=True, exist_ok=True)
seen = set()
records = []


def collect(name, parent=MODULES):
    path = parent / name
    if not path.exists():
        path = MODULES / name
    if not path.exists():
        return
    pkg = json.loads((path / 'package.json').read_text(encoding='utf-8'))
    key = pkg['name'] + '@' + pkg['version']
    if key in seen:
        return
    seen.add(key)
    record = {'name': pkg['name'], 'version': pkg['version'],
              'license': pkg.get('license'), 'repository': pkg.get('repository'), 'notices': []}
    for item in path.iterdir():
        if item.is_file() and item.name.lower().startswith(('license', 'licence', 'copying', 'notice', 'copyright')):
            dest = pkg['name'].replace('@andresaya/', '').replace('/', '-') + '-' + item.name + '.txt'
            shutil.copy2(item, LICENSES / dest)
            record['notices'].append(dest)
    records.append(record)
    for dep in pkg.get('dependencies', {}):
        collect(dep, path / 'node_modules')


for name in ['@andresaya/edge-tts', 'openai', '@anthropic-ai/sdk', 'zod']:
    collect(name)
(LICENSES / 'components.json').write_text(json.dumps(records, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
commit = '93f6dbc5905293402ebf4b6dc162d31f7e61136e'
url = 'https://codeload.github.com/andresayac/edge-tts/zip/' + commit
target = ROOT / '.tools/THIRD-PARTY-SOURCE.zip'
target.parent.mkdir(parents=True, exist_ok=True)
request = urllib.request.Request(url, headers={'User-Agent': 'claude-dafeiyu-release'})
with urllib.request.urlopen(request, timeout=60) as response:
    assert response.status == 200
    target.write_bytes(response.read())
with zipfile.ZipFile(target) as archive:
    assert archive.testzip() is None
    pkgname = next(name for name in archive.namelist() if name.count('/') == 1 and name.endswith('/package.json'))
    assert json.loads(archive.read(pkgname))['version'] == '1.9.1'
    assert any('/src/' in name and name.endswith('.ts') for name in archive.namelist())
print(json.dumps({'notices': len(records), 'sourceArchiveBytes': target.stat().st_size}))
