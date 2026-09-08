"""Build a static, API-free public demo from the checked-in historical session."""
import argparse
import json
from pathlib import Path
from extract_demo import ROOT, standalone

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, default=ROOT/'outputs/NovelGraph-Demo.html')
    parser.add_argument('--public', action='store_true')
    args = parser.parse_args()
    data = json.loads((ROOT/'examples/demo.json').read_text('utf-8'))
    standalone(data, args.out)
    if args.public:
        html = args.out.read_text('utf-8').replace('window.__BOOT__=', 'window.__PUBLIC_DEMO__=true;window.__BOOT__=', 1)
        args.out.write_text(html, 'utf-8')
    print(args.out.resolve())
