from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path('ankigarden/assets/v2_cozy_handpainted/backgrounds')
NS = {'svg': 'http://www.w3.org/2000/svg'}
ET.register_namespace('', NS['svg'])

WEATHERS = ['gentle_rain', 'fireflies', 'cloudy', 'breeze', 'sunny']
SEASONS = ['spring', 'summer', 'autumn', 'winter', 'default']


def parse_tokens(stem: str):
    weather = next((w for w in WEATHERS if stem.endswith(w)), 'sunny')
    season = next((s for s in SEASONS if stem.startswith(s + '_') or stem.startswith('default_')), 'default')
    if stem.startswith('default_'):
        season = 'default'
    return season, weather


def add_weather_overlay(parent, weather):
    if weather == 'gentle_rain':
        for i in range(10):
            x = 40 + i * 45
            ET.SubElement(parent, '{http://www.w3.org/2000/svg}line', {
                'x1': str(x), 'y1': '90', 'x2': str(x - 14), 'y2': '210',
                'stroke': '#b6c9dd', 'stroke-width': '2', 'stroke-linecap': 'round', 'opacity': '0.35'
            })
    elif weather == 'cloudy':
        ET.SubElement(parent, '{http://www.w3.org/2000/svg}rect', {
            'x': '0', 'y': '0', 'width': '512', 'height': '210', 'fill': '#b8c1cc', 'opacity': '0.12'
        })
        for x, y, r in [('120', '95', '28'), ('148', '100', '22'), ('88', '104', '20')]:
            ET.SubElement(parent, '{http://www.w3.org/2000/svg}circle', {'cx': x, 'cy': y, 'r': r, 'fill': '#f1f4f7', 'opacity': '0.22'})
    elif weather == 'fireflies':
        for x, y in [('72', '128'), ('140', '118'), ('238', '108'), ('318', '136'), ('420', '112')]:
            ET.SubElement(parent, '{http://www.w3.org/2000/svg}circle', {'cx': x, 'cy': y, 'r': '3.5', 'fill': '#ffe79d', 'opacity': '0.85'})
            ET.SubElement(parent, '{http://www.w3.org/2000/svg}circle', {'cx': x, 'cy': y, 'r': '8', 'fill': '#fff4c9', 'opacity': '0.25'})
    elif weather == 'breeze':
        for d in ['M40 120 C120 98, 180 148, 260 122 C330 102, 390 118, 470 108', 'M30 156 C98 138, 176 172, 260 150 C336 130, 402 154, 482 142']:
            ET.SubElement(parent, '{http://www.w3.org/2000/svg}path', {
                'd': d, 'fill': 'none', 'stroke': '#d9ecff', 'stroke-width': '3', 'stroke-linecap': 'round', 'opacity': '0.35'
            })
    elif weather == 'sunny':
        ET.SubElement(parent, '{http://www.w3.org/2000/svg}circle', {
            'cx': '420', 'cy': '70', 'r': '52', 'fill': '#fff0b8', 'opacity': '0.12'
        })


def add_season_tint(parent, season):
    tint = {
        'spring': ('#ffd6e8', '0.08'),
        'summer': ('#ffe8af', '0.08'),
        'autumn': ('#ffd8b0', '0.1'),
        'winter': ('#cfe4ff', '0.12'),
        'default': (None, None),
    }[season]
    if tint[0]:
        ET.SubElement(parent, '{http://www.w3.org/2000/svg}rect', {
            'x': '0', 'y': '0', 'width': '512', 'height': '384', 'fill': tint[0], 'opacity': tint[1]
        })


def process_file(path: Path):
    root = ET.fromstring(path.read_text(encoding='utf-8'))
    stem = path.stem
    season, weather = parse_tokens(stem)

    for child in list(root):
        if child.attrib.get('id') == f'{stem}__generated_overlay':
            root.remove(child)

    overlay = ET.Element('{http://www.w3.org/2000/svg}g', {'id': f'{stem}__generated_overlay'})
    add_season_tint(overlay, season)
    add_weather_overlay(overlay, weather)
    root.append(overlay)

    xml = ET.tostring(root, encoding='unicode')
    path.write_text(xml.strip() + '\n', encoding='utf-8')


def main():
    for svg in ROOT.rglob('*.svg'):
        process_file(svg)

if __name__ == '__main__':
    main()
