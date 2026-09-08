import os
import subprocess
import sys
from pathlib import Path


def find_project():
    skill = Path(__file__).resolve().parents[1]
    candidates = [Path(os.environ['NOVEL_GRAPH_LAB_HOME'])] if os.environ.get('NOVEL_GRAPH_LAB_HOME') else []
    candidates += [skill.parent.parent, Path.cwd(), skill/'assets/project']
    for path in candidates:
        if (path/'server.py').is_file():
            return path
    raise SystemExit('找不到配套项目；请设置 NOVEL_GRAPH_LAB_HOME。')


if __name__ == '__main__':
    project = find_project()
    if '--print-project' in sys.argv:
        print(project)
    else:
        raise SystemExit(subprocess.call([sys.executable, str(project/'server.py'), *sys.argv[1:]], cwd=project))
