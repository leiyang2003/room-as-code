"""Build the English project guide as self-contained HTML and print-first PDF.

Document dependencies: Markdown, WeasyPrint, pypdf. No application files changed.
"""
from pathlib import Path
import base64
import html
import json
import re
import struct
import sys

import markdown
from weasyprint import HTML
from pypdf import PdfReader

DOCS = Path(__file__).resolve().parents[1]
STEM = 'Room_Studio_Project_Guide_EN'
SOURCE = DOCS / (STEM + '.md')
IMAGES = DOCS / 'images'
LABELS = {
    'living-day': 'manhattan-living-day.png',
    'living-night': 'manhattan-living-night.png',
    'bedroom-day': 'manhattan-bedroom-day.png',
    'overview-day': 'manhattan-overview-day.png',
}

CSS = r'''
:root{--paper:#f4efe6;--paper-2:#fffdf8;--paper-3:#ece5d8;--ink:#1b1a17;--ink-2:#514d45;--ink-3:#756e61;--rule:rgba(27,26,23,.14);--shu:#b8442f;--shu-soft:rgba(184,68,47,.1);--night:#100f0d;--night-ink:#f2eee5;--serif:"Iowan Old Style",Charter,"Palatino Linotype",Palatino,Georgia,serif;--sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;--mono:ui-monospace,"SFMono-Regular",Menlo,monospace}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:90px}body{margin:0;background:var(--paper);color:var(--ink);font:17px/1.72 var(--sans);-webkit-font-smoothing:antialiased}a{color:var(--shu);text-underline-offset:4px}a:hover{color:#8e2e1e}button{font:inherit;cursor:pointer}button,a{-webkit-tap-highlight-color:transparent}:focus-visible{outline:2px solid var(--shu);outline-offset:5px}img{display:block;width:100%;height:auto}.skip{position:absolute;left:16px;top:-80px;z-index:9;background:var(--paper-2);padding:10px}.skip:focus{top:16px}
.masthead{position:absolute;top:0;left:0;right:0;z-index:2;display:flex;justify-content:space-between;align-items:center;padding:26px 4.5vw;gap:24px;color:var(--night-ink);font-size:12px;letter-spacing:.12em;text-transform:uppercase}.masthead b{font-weight:500}.masthead .edition{color:#b9b1a2;letter-spacing:.06em}.print-button{text-decoration:none;border:1px solid #766451;border-radius:4px;background:none;color:#f2eee5;padding:9px 13px;font-size:12px;letter-spacing:normal}.print-button:hover{border-color:#e0674c;color:#e0674c}
.cover{background:var(--night);color:var(--night-ink);position:relative;display:grid;grid-template-columns:1fr 1.06fr;gap:48px;min-height:780px;padding:125px 4.5vw 72px;align-items:center}.cover-copy{max-width:550px;justify-self:end}.cover h1{font:500 clamp(65px,7.7vw,114px)/.95 var(--serif);letter-spacing:-.045em;margin:0 0 24px}.cover h2{font:400 clamp(25px,2.9vw,39px)/1.15 var(--serif);margin:0 0 22px;max-width:15em}.cover p{color:#c2b9a9;font-size:16px;line-height:1.72;max-width:35em}.cover p:first-of-type{font-family:var(--serif);font-size:20px;color:var(--night-ink)}.cover p:last-child{font-size:11px;letter-spacing:.08em;text-transform:uppercase;margin-top:30px}.cover figure{margin:0;max-width:680px}.cover figure img{height:480px;object-fit:cover;object-position:47% 50%}.cover figcaption{color:#aaa18f;border-color:#3b352b;font-size:11px}
.reader-nav{position:sticky;top:0;z-index:5;background:rgba(244,239,230,.97);border-bottom:1px solid var(--rule)}.nav-inner{display:flex;gap:25px;overflow:auto;max-width:1180px;margin:auto;padding:18px 30px;scrollbar-width:thin}.reader-nav a{font-size:12px;white-space:nowrap;color:var(--ink-2);text-decoration:none}.reader-nav a[aria-current="true"]{color:var(--shu)}.reader-nav small{font:11px var(--mono);margin-right:5px}
.sheet{max-width:1060px;margin:auto;padding:78px 40px 82px;border-bottom:1px solid var(--rule)}.chapter-mark{display:flex;justify-content:space-between;align-items:center;font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);margin-bottom:22px}.chapter-mark span:first-child{font-family:var(--mono);letter-spacing:.04em}.sheet h2{font:500 clamp(33px,4.6vw,53px)/1.12 var(--serif);letter-spacing:-.025em;margin:0 0 26px;max-width:18em;text-wrap:balance}.sheet h3{font:600 25px/1.23 var(--serif);margin:30px 0 12px}.sheet p{margin:0 0 18px}.sheet>p:first-of-type{font-size:19px;line-height:1.65;color:var(--ink-2)}.sheet strong{font-weight:600}.sheet ul,.sheet ol{padding-left:22px}.sheet li{margin-bottom:9px}.sheet li::marker{color:var(--ink-3)}.sheet blockquote{font:400 26px/1.4 var(--serif);margin:30px 0;padding:24px 28px;background:var(--paper-2);border-left:2px solid var(--ink-3)}
figure{margin:29px 0 24px;break-inside:avoid}figcaption{border-top:1px solid var(--rule);margin-top:12px;padding-top:9px;color:var(--ink-2);font-size:12px;line-height:1.55}figure img{background:var(--paper-3);border-radius:4px}.table-wrap{overflow:auto;max-width:100%;margin:24px 0}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.6}th,td{text-align:left;vertical-align:top;border-bottom:1px solid var(--rule);padding:13px 15px 13px 0}th{font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--ink-2);font-weight:600;border-top:1px solid var(--ink)}td:first-child{font-weight:500;width:23%}tr:last-child td{border-bottom-color:var(--ink-3)}.sheet aside{padding:21px 25px;background:var(--paper-3);border-radius:4px;font-size:14px;line-height:1.7;margin-top:28px}.sheet aside p:last-child{margin-bottom:0}
.principles{display:grid;grid-template-columns:repeat(3,1fr);gap:25px;margin:28px 0;border-top:1px solid var(--rule)}.principles h3{font-size:21px;margin-top:22px}.principles p{font-size:15px;color:var(--ink-2)}.facts{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;border-top:1px solid var(--rule);border-bottom:1px solid var(--rule);padding:19px 0;margin:25px 0}.facts p{font-size:12px;color:var(--ink-2);margin:0!important;border-left:1px solid var(--rule);padding-left:20px}.facts p:first-child{border:0;padding-left:0}.facts strong{font:500 34px/1.2 var(--serif);color:var(--ink)}
.pipeline{list-style:none;padding:0!important;margin:30px 0;display:grid;gap:0}.pipeline li{display:grid;grid-template-columns:48px 1fr;gap:20px;margin:0;padding:17px 0;border-top:1px solid var(--rule)}.pipeline li:last-child{border-bottom:1px solid var(--rule)}.pipeline li>span{font:18px var(--serif);color:var(--ink-3)}.pipeline b{font:600 21px/1.2 var(--serif)}.pipeline p{font-size:15px;color:var(--ink-2);margin:6px 0 0}.edit-example{border:1px solid var(--rule);background:var(--paper-2);border-radius:6px;padding:23px 28px;margin:28px 0}.edit-example p:nth-child(2){font:25px/1.4 var(--serif)}.edit-example p:last-child{margin-bottom:0}
code{font: .83em/1.5 var(--mono);overflow-wrap:anywhere}pre{padding:17px 19px;background:var(--paper-2);border:1px solid var(--rule);border-radius:4px;overflow:auto;font-size:13px;line-height:1.7;white-space:pre-wrap;word-break:normal;overflow-wrap:anywhere}pre code{font-size:inherit;overflow-wrap:normal}.daynight{margin:25px 0}.view-controls{display:flex;align-items:center;gap:8px;margin-bottom:14px}.view-controls span{font-size:12px;margin-right:auto;color:var(--ink-2)}.view-controls button{font-size:12px;padding:7px 18px;border-radius:4px;border:1px solid var(--rule);background:var(--paper-2);color:var(--ink-2)}.view-controls button[aria-pressed=true]{background:var(--shu);border-color:var(--shu);color:#fffdf8}.view-controls button:focus-visible{outline-offset:3px}.daynight figure{margin:0}.daynight .night-view{display:none}.daynight[data-view=night] .day-view{display:none}.daynight[data-view=night] .night-view{display:block}.doc-footer{max-width:1060px;margin:0 auto;padding:35px 40px 55px;font-size:12px;color:var(--ink-2);display:flex;justify-content:space-between;gap:24px}.print-only{display:none}
@media(max-width:780px){.cover{grid-template-columns:1fr;gap:24px;min-height:0;padding:112px 25px 38px}.cover-copy{justify-self:start;max-width:100%}.cover h1{font-size:69px;max-width:8em}.cover p{max-width:45em}.cover figure{max-width:none}.cover figure img{height:auto;aspect-ratio:11/7.7}.masthead{padding:23px 25px}.masthead .edition{display:none}.sheet{padding:52px 25px 55px}.reader-nav .nav-inner{padding:15px 25px;gap:21px}.principles{grid-template-columns:1fr;gap:0}.principles h3{margin-top:16px}.principles p{margin-bottom:3px}.facts{gap:10px}.facts strong{font-size:28px}.facts p{padding-left:10px;font-size:10px}.sheet>p:first-of-type{font-size:17px}.sheet blockquote{font-size:23px;padding:20px}.chapter-mark{font-size:10px}table{min-width:570px}.doc-footer{padding:28px 25px;flex-direction:column;gap:6px}.sheet h3{font-size:23px}}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
@page{size:A4;margin:17mm 17mm 17mm;background:#fffdf8;@top-left{content:"ROOM AS CODE";font-family:Arial,sans-serif;font-size:7.5pt;letter-spacing:1.1pt;color:#756e61;vertical-align:middle;border-bottom:.3pt solid #d9d2c6;padding-bottom:3mm}@top-right{content:"PROJECT GUIDE  /  0.1";font-family:Arial,sans-serif;font-size:7pt;color:#756e61;vertical-align:middle;border-bottom:.3pt solid #d9d2c6;padding-bottom:3mm}@bottom-left{content:"7 NOVEMBER 2026  ·  ENGLISH EDITION";font-family:Arial,sans-serif;font-size:6.8pt;color:#756e61}@bottom-right{content:counter(page);font-family:Georgia,serif;font-size:9pt;color:#514d45}}
@page:first{@top-left{content:none}@top-right{content:none}}
@media print{html{scroll-behavior:auto}body{background:#fffdf8;font-family:Arial,sans-serif;font-size:10pt;line-height:1.43;print-color-adjust:exact;-webkit-print-color-adjust:exact}.masthead,.reader-nav,.skip,.doc-footer,.view-controls{display:none}.sheet{max-width:none;margin:0;padding:8mm 0 0;border:0;break-before:page;page-break-before:always}.chapter-mark{font-size:7pt;letter-spacing:1pt;margin-bottom:5mm}.sheet h2{font-size:31pt;line-height:1.08;margin:0 0 6mm;max-width:none;letter-spacing:-.6pt}.sheet h3{font-size:15pt;line-height:1.2;margin:6mm 0 2.6mm;break-after:avoid}.sheet p{margin-bottom:3.6mm;orphans:3;widows:3}.sheet>p:first-of-type{font-size:11.5pt;line-height:1.5;color:#514d45}.sheet aside{font-size:9pt;line-height:1.45;padding:4mm 5mm;margin-top:5mm;break-inside:avoid;background:#f0ebe2}.sheet blockquote{font-size:15pt;line-height:1.35;margin:5mm 0;padding:4mm 5mm;break-inside:avoid}.table-wrap{margin:5mm 0;overflow:visible}table{font-size:9pt;line-height:1.4;min-width:0;width:100%;table-layout:fixed}th,td{padding:2.8mm 3mm 2.8mm 0;overflow-wrap:anywhere}th{font-size:7pt;letter-spacing:.4pt}td:first-child{width:auto}tr{break-inside:avoid}thead{display:table-header-group}.sheet figure{margin:5mm 0 4mm}figcaption{font-size:7.5pt;line-height:1.4;margin-top:2mm;padding-top:2mm}figure img{border-radius:1mm}.facts{margin:4mm 0;padding:3.5mm 0;gap:3mm}.facts p{font-size:7pt;padding-left:4mm}.facts strong{font-size:24pt}.principles{gap:5mm;margin:5mm 0}.principles h3{font-size:13pt;margin:4mm 0 2mm}.principles p{font-size:9pt;line-height:1.45}.pipeline{margin:5mm 0}.pipeline li{grid-template-columns:9mm 1fr;gap:4mm;padding:2.2mm 0;break-inside:avoid}.pipeline li>span{font-size:12pt}.pipeline b{font-size:14pt}.pipeline p{font-size:9.5pt;line-height:1.4;margin:1.4mm 0 0}.edit-example{padding:4mm 5mm;margin:5mm 0;break-inside:avoid}.edit-example p:nth-child(2){font-size:15pt;line-height:1.32}.edit-example p:last-child{font-size:9.5pt}pre{font-size:8.4pt;line-height:1.55;padding:3.2mm 4mm;margin:3mm 0 4mm;break-inside:avoid}code{font-size:.83em}.daynight{display:grid;grid-template-columns:1fr 1fr;gap:4mm;margin:5mm 0}.daynight .day-view,.daynight .night-view{display:block!important}.daynight figure{margin:0}.daynight figcaption{font-size:7pt}a{color:#8e3021;text-decoration:none}#apartment>figure img{max-height:92mm;object-fit:contain}#outputs>figure img{max-height:82mm;object-fit:cover}#scope{font-size:9.7pt}.cover{display:block;min-height:0;margin:0;padding:7mm 7mm 6mm;background:#100f0d;break-inside:avoid;color:#f2eee5}.cover-copy{max-width:none}.cover h1{font-size:57pt;line-height:1;margin:0 0 4mm;letter-spacing:-1.9pt}.cover h2{font-size:23pt;line-height:1.15;max-width:none;margin:0 0 5mm}.cover p{font-size:10pt;line-height:1.5;max-width:none;margin:0 0 4mm}.cover p:first-of-type{font-size:12.5pt;line-height:1.45}.cover p:last-child{font-size:7pt;margin-top:5mm}.cover figure{max-width:none;margin-top:5mm}.cover figure img{height:87mm;width:100%;object-fit:cover}.cover figcaption{font-size:7pt;line-height:1.35;padding-top:2mm;margin-top:2mm}.print-only{display:block}.screen-only{display:none}}
.output-grid{display:grid;grid-template-columns:.95fr 1.05fr;gap:28px;align-items:start;margin:28px 0}.output-grid figure,.output-grid .table-wrap{margin:0}.output-grid td:first-child{width:30%}
@media(max-width:780px){.output-grid{grid-template-columns:1fr;gap:18px}.output-grid table{min-width:0}}
@media print{h1,h2,h3{font-family:var(--serif);font-weight:500}.cover h1,.cover h2{font-family:var(--serif);font-weight:500}.sheet{font-size:10.5pt;line-height:1.44}.sheet h2{font-family:var(--serif);font-size:30pt}.sheet h3{margin-top:4.5mm}.table-wrap table{font-size:9.2pt}.table-wrap th:first-child{width:25%}.table-wrap th,.table-wrap td{padding-top:2.3mm;padding-bottom:2.3mm}.edit-example p:nth-child(2){font-size:14pt}.output-grid{grid-template-columns:.85fr 1.15fr;gap:5mm;margin:5mm 0;break-inside:avoid}.output-grid figure,.output-grid .table-wrap{margin:0}.output-grid figure img{max-height:none;object-fit:contain}.output-grid table{font-size:9pt}.output-grid th:first-child{width:28%}.output-grid td,.output-grid th{padding-top:2mm;padding-bottom:2mm}.output-grid figcaption{font-size:8pt}.daynight figcaption{font-size:8pt}.sheet figcaption{font-size:8pt}}
'''


def data_uri(key):
    data = (IMAGES / LABELS[key]).read_bytes()
    if data[:8] != b'\x89PNG\r\n\x1a\n':
        raise ValueError('Expected a PNG render')
    clean = bytearray(data[:8])
    offset = 8
    while offset < len(data):
        length = struct.unpack('>I', data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        end = offset + length + 12
        if kind not in (b'tEXt', b'iTXt', b'zTXt', b'eXIf', b'tIME'):
            clean.extend(data[offset:end])
        offset = end
    return 'data:image/png;base64,' + base64.b64encode(clean).decode()


def figure(key, caption, cls=''):
    return (f'<figure class="{cls}"><img src="{data_uri(key)}" '
            f'alt="{html.escape(caption, quote=True)}" width="1100" height="770">'
            f'<figcaption>{html.escape(caption)}</figcaption></figure>')


def enrich(text):
    def picture(match):
        return figure(match.group(1), match.group(2))
    text = re.sub(r'\{\{image:([^|]+)\|([^}]+)\}\}', picture, text)
    gallery = ('<div class="daynight" data-view="day">'
               '<div class="view-controls"><span>Same scene / two lighting templates</span>'
               '<button type="button" data-select="day" aria-pressed="true">Day</button>'
               '<button type="button" data-select="night" aria-pressed="false">Night</button></div>'
               + figure('living-day', 'Day / sky and sun with the saved interior setup.', 'day-view')
               + figure('living-night', 'Night / concealed lighting with the night environment.', 'night-view')
               + '</div>')
    text = text.replace('{{daynight}}', gallery)
    text = re.sub(r'<p>\s*(<figure.*?</figure>)\s*</p>', r'\1', text, flags=re.S)
    text = re.sub(r'<p>\s*(<div class="daynight".*?</div></div>)\s*</p>', r'\1', text, flags=re.S)
    text = re.sub(r'<table>(.*?)</table>', r'<div class="table-wrap"><table>\1</table></div>', text, flags=re.S)
    def principles(match):
        parts = re.split(r'(?=<h3>)', match.group(1))
        return '<div class="principles">' + ''.join('<article>' + p + '</article>' for p in parts if p.strip()) + '</div>'
    text = re.sub(r'<div class="principles">(.*?)</div>', principles, text, flags=re.S)
    return text


def build():
    source = SOURCE.read_text()
    parts = re.split(r'<!-- page: ([a-z-]+) \| ([^>]+) -->', source)[1:]
    chapters = []
    nav = []
    for i in range(0, len(parts), 3):
        ident, label, raw = parts[i:i + 3]
        number = i // 3
        body = enrich(markdown.markdown(raw.strip(), extensions=['extra', 'sane_lists']))
        if ident == 'outputs':
            body = re.sub(r'(<figure.*?</figure>)\s*(<div class="table-wrap">.*?</div>)', r'<div class="output-grid">\1\2</div>', body, count=1, flags=re.S)
        if ident == 'cover':
            match = re.search(r'<figure.*?</figure>', body, re.S)
            art = match.group(0)
            copy = body[:match.start()] + body[match.end():]
            chapters.append('<header class="cover" id="cover"><div class="cover-copy">' + copy + '</div>' + art + '</header>')
        else:
            chapters.append(f'<section class="sheet" id="{ident}" aria-label="{html.escape(label)}">'
                            f'<div class="chapter-mark"><span>{number:02d} / {html.escape(label)}</span><span>Room as Code</span></div>'
                            + body + '</section>')
            nav.append(f'<a href="#{ident}"><small>{number:02d}</small>{html.escape(label)}</a>')
    script = r'''

document.querySelectorAll('.view-controls button').forEach(button=>{
button.addEventListener('click',()=>{
 const gallery=button.closest('.daynight');gallery.dataset.view=button.dataset.select;
 gallery.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(b===button)));
});
button.addEventListener('keydown',event=>{if(!['ArrowLeft','ArrowRight'].includes(event.key))return;event.preventDefault();const all=[...button.parentElement.querySelectorAll('button')];const next=all[(all.indexOf(button)+1)%all.length];next.click();next.focus()});
});
if('IntersectionObserver' in window){
 const observer=new IntersectionObserver(entries=>{for(const entry of entries){if(entry.isIntersecting)document.querySelectorAll('.reader-nav a').forEach(a=>a.setAttribute('aria-current',String(a.hash==='#'+entry.target.id))) }},{rootMargin:'-12% 0px -62% 0px'});document.querySelectorAll('.sheet').forEach(s=>observer.observe(s));}
'''
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="description" content="Room as Code: a project guide to conversational 3D interiors with persistent state, reversible edits, local previews and Blender exports.">'
            '<meta name="author" content="Room as Code contributors">'
            '<title>Room as Code - Project Guide</title><style>' + CSS + '</style></head><body>'
            '<a class="skip" href="#purpose">Skip to the guide</a>'
            '<div class="masthead"><b>Room as Code</b><span class="edition">Project guide / November 2026</span>'
            '<a class="print-button" href="Room_Studio_Project_Guide_EN.pdf">Read PDF</a></div>'
            + chapters[0] + '<nav class="reader-nav" aria-label="Guide contents"><div class="nav-inner">'
            + ''.join(nav) + '</div></nav><main id="guide">' + ''.join(chapters[1:]) + '</main>'
            '<footer class="doc-footer"><span>Room as Code / Built with Room Studio 0.1</span><span>English project guide · 7 November 2026</span></footer>'
            '<script id="document-source" type="application/json">' + json.dumps(source).replace('</', r'<\/') + '</script>'
            '<script>' + script + '</script></body></html>')
    html_path = DOCS / (STEM + '.html')
    pdf_path = DOCS / (STEM + '.pdf')
    html_path.write_text(page)
    HTML(string=page, base_url=str(DOCS)).write_pdf(str(pdf_path), presentational_hints=True)
    pdf = PdfReader(str(pdf_path))
    report = {'html': html_path.name, 'pdf': pdf_path.name, 'pages': len(pdf.pages),
              'chapters': len(chapters), 'embedded_image_uses': page.count('data:image/png;base64,'),
              'page_text_characters': [len(p.extract_text() or '') for p in pdf.pages],
              'design_reference': 'Approved paper-and-ink project guide',
              'design': 'paper/ink, shu interactions, Latin book serif, night-to-paper opening',
              'render_engine': 'WeasyPrint', 'status': 'GENERATED; visual review required'}
    qa = DOCS / 'qa/project-guide'
    qa.mkdir(parents=True, exist_ok=True)
    (qa / 'build-results.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    build()
