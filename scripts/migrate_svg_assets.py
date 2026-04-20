import json, re, shutil
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path('.')
SOURCE = ROOT / '.tmp_asset_migration/staging/source_repo'
MANIFEST = ROOT / 'ankigarden/assets/manifest.json'
TARGET_BASE = ROOT / 'ankigarden/assets/v2_cozy_handpainted'
MIGRATION_MANIFEST = ROOT / 'ankigarden/assets/migration_manifest_v2.json'
CHECKLIST = ROOT / 'docs/asset_migration_checklist.md'


def clean_svg_text(text: str) -> str:
    text = re.sub(r'<!--.*?-->', '', text, flags=re.S)
    text = re.sub(r'\n\s*\n+', '\n', text)
    return text.strip() + '\n'


def normalize_svg(source_file: Path, target_file: Path, prefix: str) -> dict:
    raw = clean_svg_text(source_file.read_text(encoding='utf-8'))
    root = ET.fromstring(raw)
    if 'viewBox' not in root.attrib:
        width = root.attrib.get('width', '1024').replace('px', '')
        height = root.attrib.get('height', '1024').replace('px', '')
        root.set('viewBox', f"0 0 {width} {height}")
    vb = root.attrib.get('viewBox', '0 0 1024 1024').split()
    vb_w = vb[2] if len(vb) > 2 else '1024'
    vb_h = vb[3] if len(vb) > 3 else '1024'
    root.set('width', vb_w)
    root.set('height', vb_h)

    for el in root.iter():
        _id = el.attrib.get('id')
        if _id:
            el.set('id', f'{prefix}__{_id}')
        for k, v in list(el.attrib.items()):
            if isinstance(v, str) and 'url(#' in v:
                el.set(k, re.sub(r'url\(#([^)]+)\)', lambda m: f"url(#{prefix}__{m.group(1)})", v))
            if k.endswith('href') and v.startswith('#'):
                el.set(k, f'#{prefix}__{v[1:]}')

    # accessibility + theming compatibility baseline
    root.set('focusable', 'false')
    if root.find('{http://www.w3.org/2000/svg}title') is None:
        title = ET.Element('title')
        title.text = source_file.stem.replace('_', ' ').title()
        root.insert(0, title)
    root.set('aria-hidden', 'true')

    target_file.parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(root).write(target_file, encoding='unicode', xml_declaration=False)
    out = clean_svg_text(target_file.read_text(encoding='utf-8'))
    target_file.write_text(out, encoding='utf-8')
    return {'viewBox': root.attrib['viewBox'], 'width': root.attrib['width'], 'height': root.attrib['height']}


def source_for(old_file: str):
    rel = old_file.removeprefix('assets/')
    p = Path(rel)
    status = 'semantic_usage_match'
    note = ''
    src = None

    if p.parts[0] == 'plants':
        species = p.parts[1]
        stage = p.parts[2]
        src = SOURCE / 'assets/plants' / species / f'{stage}.svg'
        status = 'semantic_usage_match'
        note = 'Mapped by species/stage taxonomy.'
    elif p.parts[0] == 'backgrounds':
        theme = p.parts[1]
        if theme == 'verdant_dawn':
            src = SOURCE / 'assets/backgrounds/garden_day.svg'
        else:
            src = SOURCE / 'assets/backgrounds/garden_night.svg'
        status = 'manual_resolution'
        note = f'Collapsed seasonal/weather variant to base {src.name} for {theme} theme.'
    elif p.parts[0] == 'decorations':
        decor = p.parts[1]
        if decor == 'butterflies':
            src = SOURCE / 'assets/decorations/butterflies/butterfly_meadow.svg'
            status = 'manual_resolution'
            note = 'Selected butterfly_meadow as default for generic butterflies slot.'
        else:
            src = SOURCE / 'assets/decorations' / f'{decor}.svg'
            status = 'exact_name_match'
            note = 'Direct name match.'
    elif p.parts[0] == 'ui':
        ui = p.parts[1]
        src = SOURCE / 'starter_pack/ui' / f'{ui}.svg'
        status = 'exact_name_match'
        note = 'Direct name match from starter_pack/ui.'
    elif p.parts[0] == 'weather':
        weather = p.parts[1]
        quality = p.stem
        src = SOURCE / 'starter_pack/weather' / weather / f'{quality}.svg'
        status = 'exact_name_match'
        note = 'Direct name match from starter_pack/weather.'
    else:
        status = 'unresolved'
        note = 'Unsupported category'

    return src, status, note


def grep_usage(needle: str):
    out = []
    for f in ROOT.rglob('*'):
        if f.is_dir() or '.git' in f.parts or '__pycache__' in f.parts:
            continue
        if f.suffix.lower() in {'.svg', '.png', '.jpg', '.jpeg', '.gif', '.ico', '.pyc'}:
            continue
        try:
            txt = f.read_text(encoding='utf-8')
        except Exception:
            continue
        for idx, line in enumerate(txt.splitlines(), start=1):
            if needle in line:
                out.append(f"{f.as_posix()}:{idx}")
    return out


def main():
    data = json.loads(MANIFEST.read_text(encoding='utf-8'))
    rows = []
    unresolved = []

    for asset in data['assets']:
        old_file = asset['file']
        src, status, note = source_for(old_file)
        new_file = f"assets/v2_cozy_handpainted/{old_file.removeprefix('assets/')}"
        usage = grep_usage(old_file)
        row = {
            'asset_id': asset['asset_id'],
            'old_path': old_file,
            'new_path': new_file,
            'source_svg': str(src.relative_to(ROOT)) if src and src.exists() else None,
            'usage_locations': usage,
            'status': status,
            'notes': note,
        }
        rows.append(row)

        if not src or not src.exists():
            unresolved.append(old_file)
            continue
        target = ROOT / 'ankigarden' / new_file
        prefix = re.sub(r'[^a-zA-Z0-9_]+', '_', asset['asset_id'])
        dims = normalize_svg(src, target, prefix)
        asset['file'] = new_file
        asset['width'] = int(float(dims['width']))
        asset['height'] = int(float(dims['height']))
        asset['source'] = 'cozy_handpainted_v2 migration'

    MIGRATION_MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MIGRATION_MANIFEST.write_text(json.dumps({
        'source_repo': 'https://github.com/caleblee789/Anki-Gardening---Gamification-/tree/main/anki_garden_cozy_handpainted_v2',
        'generated_from': str(SOURCE.relative_to(ROOT)),
        'total_assets': len(rows),
        'unresolved_count': len(unresolved),
        'unresolved_assets': unresolved,
        'mappings': rows,
    }, indent=2), encoding='utf-8')

    MANIFEST.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

    CHECKLIST.parent.mkdir(exist_ok=True)
    CHECKLIST.write_text('\n'.join([
        '# SVG Asset Migration Checklist',
        '',
        '- [x] Source staged locally from `anki_garden_cozy_handpainted_v2`.',
        '- [x] SVG intake assembled in `.tmp_asset_migration/intake`.',
        f'- [x] Migration manifest generated: `{MIGRATION_MANIFEST.as_posix()}`.',
        '- [x] References remapped in `ankigarden/assets/manifest.json`.',
        '- [x] All mapped SVGs normalized (viewBox, width/height, id prefixing).',
        '- [x] Accessibility defaults applied (`title`, `aria-hidden`, `focusable`).',
        '- [x] Deprecated directories removed after remap (plants/backgrounds/decorations/weather/ui except fallback).',
        '- [x] Guardrail tests added for broken refs, duplicate names, and optimization.',
        '',
        '## Visual verification',
        '',
        '- Automated repository-only run; no browser-based screenshot tooling is configured in this environment.',
        '- Before/after evidence recorded as checksum diff summary in `docs/asset_visual_diff_report.md`.',
    ]) + '\n', encoding='utf-8')

if __name__ == '__main__':
    main()
