"""Build portable project/skill distributions from an explicit file allowlist."""
import hashlib
import argparse
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = ['kernel_build.py', 'kernel_retrieve.py', 'research_prompts.py', 'core.py', 'server.py', 'cli.py', 'start.cmd', 'README.md', 'README.zh-CN.md', 'QA.md', '.gitignore', 'LICENSE', 'NOTICE.md', 'CONTRIBUTING.md', 'SECURITY.md', 'CITATION.cff']
DIRS = ['web', 'examples', 'tests', 'tools', 'docs', '.github']


def sources():
    yield from (ROOT/f for f in FILES)
    for folder in DIRS:
        yield from (p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--update-installed', action='store_true')
    args = parser.parse_args()
    skill = ROOT/'skill/novel-graph-lab'
    assets = skill/'assets/project'
    for src in sources():
        target = assets/src.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, target)
    installed = Path.home()/'.codex/skills/novel-graph-lab'
    if installed.exists() and not args.update_installed:
        raise SystemExit(f'Existing skill preserved: {installed}. Update explicitly if intended.')
    shutil.copytree(skill, installed, dirs_exist_ok=args.update_installed)
    (ROOT/'dist').mkdir(exist_ok=True)
    with zipfile.ZipFile(ROOT/'dist/novel-graph-lab-project.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for src in sources():
            z.write(src, Path('novel-graph-lab')/src.relative_to(ROOT))
        z.write(ROOT/'outputs/NovelGraph-Demo.html', 'novel-graph-lab/outputs/NovelGraph-Demo.html')
        for src in skill.rglob('*'):
            if src.is_file() and '__pycache__' not in src.parts:
                z.write(src, Path('novel-graph-lab/skill/novel-graph-lab')/src.relative_to(skill))
    with zipfile.ZipFile(ROOT/'dist/novel-graph-lab-skill.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for src in skill.rglob('*'):
            if src.is_file() and '__pycache__' not in src.parts:
                z.write(src, Path('novel-graph-lab')/src.relative_to(skill))
    manifest = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources()}
    (ROOT/'dist/manifest.json').write_text(json.dumps(manifest, indent=2), 'utf-8')
    print('Installed skill:', installed)
    print('Distributions:', ROOT/'dist')
