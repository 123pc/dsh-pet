"""Patch the installed version in a staging copy; preserve unrelated runtime customizations."""
import argparse
import hashlib
import json
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[1]


def replace_one(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f'Expected one compatible patch location, found {text.count(old)}: {old[:90]}')
    return text.replace(old, new, 1)


def build(runtime, node, apply=False, base_backup=None):
    package = json.loads((runtime / 'package.json').read_text(encoding='utf-8'))
    if package['name'] != 'dsh-pet': raise ValueError('Not a dsh-pet runtime')
    if not base_backup and 'companion-runtime-v1' in (runtime / 'runtime/electron-helper/shared-core.js').read_text(encoding='utf-8'):
        raise ValueError('This runtime already has companion-runtime-v1; use the recorded backup for a fresh rebuild.')
    work = REPO / '.tools/companion-runtime' / datetime.now().strftime('%Y%m%d-%H%M%S')
    stage, backup = work / 'stage', work / 'backup'
    stage.mkdir(parents=True)
    for part in ('src/client', 'src/shared'):
        shutil.copytree(runtime / part, stage / part)
    files = ['runtime/electron-helper/sprite.js', 'runtime/electron-helper/events.js',
             'runtime/electron-helper/shared-core.js', 'lib/client.js']
    for name in files:
        (backup / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(runtime / name, backup / name)
    def read(name): return ((base_backup / name) if base_backup and name in files else (runtime / name)).read_text(encoding='utf-8')
    def save(name, text):
        target = stage / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding='utf-8')
    repo_pet = (REPO / 'dsh-pet/src/client/pet.ts').read_text(encoding='utf-8')
    helper = repo_pet[repo_pet.index('    const workPhaseRef'):repo_pet.index('    // 调试日志：上一档位')]
    browser = read('src/client/pet.ts')
    browser = replace_one(browser, "import { WORK_STATUS_INDEX, type WorkStatusSnapshot } from '../shared/work-status';",
                          "import { WORK_STATUS_INDEX, type WorkStatusSnapshot } from '../shared/work-status';\nimport { advanceWorkSequence, isWorkSequenceAnim, type WorkPhase } from '../shared/work-sequence';")
    browser = replace_one(browser, '    const prevWorkTickRef = useRef(0);', '    const prevWorkTickRef = useRef(0);\n' + helper.rstrip())
    browser = replace_one(browser, '      if (!workStatus || workStatus.state === null) {',
                          '      const sequenceHandled = stepWorkSequence(workStatus?.state);\n      if (!workStatus || workStatus.state === null) {')
    browser = replace_one(browser, 'if (poolIncludes(petAnims.events?.workStatus ?? [], animRef.current)) {',
                          'if (!sequenceHandled && poolIncludes(petAnims.events?.workStatus ?? [], animRef.current)) {')
    browser = replace_one(browser, '      const rotating = !terminal && Array.isArray(slot) && slot.length > 1;',
                          '      if (sequenceHandled) return;\n      const rotating = !terminal && Array.isArray(slot) && slot.length > 1;')
    anchor = "      if (!ws || !ws.state || ws.state === 'success' || ws.state === 'error') return false;"
    start = repo_pet.index(anchor) + len(anchor)
    resume = repo_pet[start:repo_pet.index('      const pool = petAnims.events?.workStatus;', start)]
    browser = replace_one(browser, anchor, anchor + resume.rstrip())
    start = re.search(r'      if \(\s*animations\.workSequence &&',repo_pet).start()
    end = repo_pet.index('      // 事件动画播完回 idle', start)
    browser = replace_one(browser, '      const isEvent = isEventAnim(animations.events, animRef.current);',
                          repo_pet[start:end] + '      const isEvent = isEventAnim(animations.events, animRef.current);')
    save('src/client/pet.ts', browser)
    types = read('src/shared/types.ts')
    types = replace_one(types, '  events: Events;\n}', '  events: Events;\n  workSequence?: WorkSequence;\n}\nexport interface WorkSequence { enter: string; loops: string[]; exit: string; }')
    save('src/shared/types.ts', types)
    shutil.copyfile(REPO / 'dsh-pet/src/shared/work-sequence.ts', stage / 'src/shared/work-sequence.ts')
    # Keep installed rendering/styles and replace only the menu's pure tree builder.
    repo_menu = (REPO / 'dsh-pet/src/shared/menu.ts').read_text(encoding='utf-8')
    menu = read('src/shared/menu.ts')
    def menu_builder(text):
        start = text.index('export function buildMenuTree(')
        end = text.index('\n}\n',start)+3
        return text[start:end]
    menu = replace_one(menu,menu_builder(menu),menu_builder(repo_menu))
    menu = replace_one(menu,"  workStatus: '工作状态',","  workStatus: '工作状态',\n  workTransition: '办公衔接',")
    save('src/shared/menu.ts',menu)

    repo_sprite = (REPO / 'dsh-pet/runtime/electron-helper/sprite.js').read_text(encoding='utf-8')
    sprite = read('runtime/electron-helper/sprite.js')
    sprite = sprite.replace('    this.once = true;', "    this.once = true;\n    this.workPhase = 'closed';", 1)
    start = re.search(r'    if \(\s*animations\.workSequence &&',repo_sprite).start()
    end = repo_sprite.index('    // 事件动画播完', start)
    sprite = replace_one(sprite, '    const isEvent = S.isEventAnim(animations.events, this.anim);',
                         repo_sprite[start:end] + '    const isEvent = S.isEventAnim(animations.events, this.anim);')
    anchor = "    if (!state || state === 'success' || state === 'error') return false;"
    start = repo_sprite.index(anchor) + len(anchor)
    resume = repo_sprite[start:repo_sprite.index('    const pool = this.animations.events?.workStatus;', start)]
    sprite = replace_one(sprite, anchor, anchor + resume.rstrip())
    start = repo_sprite.index('  stepWorkSequence(state, ended = false) {')
    end = repo_sprite.index('\n  // 漫游', start)
    sprite = replace_one(sprite, '  resumeWorkStatusAnim() {', repo_sprite[start:end] + '\n\n  resumeWorkStatusAnim() {')
    save('runtime/electron-helper/sprite.js', sprite)
    events = read('runtime/electron-helper/events.js')
    events = replace_one(events, '  this.prevWorkState = state;', '  this.prevWorkState = state;\n  const sequenceHandled = this.stepWorkSequence(state);')
    events = replace_one(events, 'if (S.poolIncludes(this.animations.events?.workStatus ?? [], this.anim)) {',
                         'if (!sequenceHandled && S.poolIncludes(this.animations.events?.workStatus ?? [], this.anim)) {')
    events = replace_one(events, '  const rotating = !terminal && Array.isArray(slot) && slot.length > 1;',
                         '  if (sequenceHandled) return;\n  const rotating = !terminal && Array.isArray(slot) && slot.length > 1;')
    save('runtime/electron-helper/events.js', events)
    modules = REPO / '.tools/motion-build/node_modules/rolldown/dist/esm/index.mjs'
    # Build against the installed source snapshot, retaining its UI and API version.
    script = work / 'build.mjs'
    save('menu-cleanup-entry.ts',"export { buildMenuTree } from './src/shared/menu';\n")
    script.write_text("import { rolldown } from " + json.dumps(modules.as_uri()) + ";\n" +
        "const root=" + json.dumps(str(stage)) + ";\n" +
        "const b=await rolldown({input:root+'/src/client/index.ts',platform:'browser',external:[/^@deepseek-ai\\//,/^react(?:\\/|$)/]});\n" +
        "await b.write({format:'iife',file:root+'/lib/client.js'});\n" +
        "const s=await rolldown({input:root+'/src/shared/work-sequence.ts',platform:'browser'});\n" +
        "await s.write({format:'iife',name:'PetWorkSequence',file:root+'/sequence-core.js'});\n" +
        "const m=await rolldown({input:root+'/menu-cleanup-entry.ts',platform:'browser'});\n" +
        "await m.write({format:'iife',name:'PetMenuCleanup',file:root+'/menu-core.js'});\n", encoding='utf-8')
    subprocess.run([str(node), str(script)], check=True)
    save('runtime/electron-helper/shared-core.js', read('runtime/electron-helper/shared-core.js') +
         '\n/* companion-runtime-v1: additive sequence helper */\n' + (stage / 'sequence-core.js').read_text(encoding='utf-8') +
         '\nObject.assign(window.PetShared, PetWorkSequence);\n' +
         '\n/* menu-cleanup-v1: one entry per animation */\n' + (stage / 'menu-core.js').read_text(encoding='utf-8') +
         '\nObject.assign(window.PetShared, PetMenuCleanup);\n')
    for name in files:
        subprocess.run([str(node), '--check', str(stage / name)], check=True)
    report = {'runtime': str(runtime), 'version': package['version'], 'backup': str(backup), 'stage': str(stage),
              'applied': apply, 'files': [{'file': f, 'before': hashlib.sha256((runtime / f).read_bytes()).hexdigest(),
                        'after': hashlib.sha256((stage / f).read_bytes()).hexdigest()} for f in files]}
    (work / 'deployment.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    if apply:
        try:
            for name in files: shutil.copyfile(stage / name, runtime / name)
        except Exception:
            for name in files: shutil.copyfile(backup / name, runtime / name)
            raise
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime', type=Path, required=True)
    parser.add_argument('--node', type=Path, default=Path('D:/tool/nodejs/node.exe'))
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--base-backup',type=Path,help='Explicit original four-file backup when updating a previous companion patch')
    args = parser.parse_args()
    build(args.runtime.resolve(), args.node.resolve(), args.apply, args.base_backup.resolve() if args.base_backup else None)
