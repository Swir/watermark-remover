#!/usr/bin/env python3
"""Generate/check SWIR Progress SVG PRO assets for Watermark Remover Pro."""
from __future__ import annotations
import argparse,re,sys
from pathlib import Path
import xml.etree.ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'assets'/'readme'; README=ROOT/'README.md'
LEGACY=(re.compile(r'[█▓▒░]{4,}'),re.compile(r'\[(?:[#=\-]{4,})\]'))
CARD='''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="180" viewBox="0 0 1200 180" role="img" aria-labelledby="title desc"><title id="title">Watermark Remover Pro progress</title><desc id="desc">Product roadmap progress is N/A because no authoritative measurable product roadmap exists.</desc><defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#02050A"/><stop offset="1" stop-color="#07111C"/></linearGradient><linearGradient id="a" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#0088FF"/><stop offset="1" stop-color="#62E5FF"/></linearGradient></defs><rect x="1" y="1" width="1198" height="178" rx="22" fill="url(#bg)" stroke="#62E5FF" stroke-opacity=".25"/><text x="50" y="38" fill="#62E5FF" font-family="Segoe UI,Arial,sans-serif" font-size="15" font-weight="700" letter-spacing="3">SWIR PROGRESS</text><text x="50" y="73" fill="#F4FAFF" font-family="Segoe UI,Arial,sans-serif" font-size="27" font-weight="800">Watermark Remover Pro</text><text x="50" y="100" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="14">Product roadmap</text><text x="1138" y="73" text-anchor="end" fill="#F4FAFF" font-family="Segoe UI,Arial,sans-serif" font-size="32" font-weight="800">N/A</text><text x="1138" y="99" text-anchor="end" fill="#62E5FF" font-family="Segoe UI,Arial,sans-serif" font-size="13" font-weight="700">NO VERIFIED ROADMAP</text><rect x="50" y="119" width="1100" height="18" rx="9" fill="#08131F" stroke="#62E5FF" stroke-opacity=".16"/><path d="M68 128H1132" stroke="url(#a)" stroke-width="2" stroke-dasharray="8 12" opacity=".34"/><text x="50" y="160" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="12">N/A — release state is known; overall product completion is not defined by a canonical roadmap</text></svg>'''
MINI='''<svg xmlns="http://www.w3.org/2000/svg" width="900" height="72" viewBox="0 0 900 72" role="img" aria-labelledby="title desc"><title id="title">Watermark Remover Pro compact progress</title><desc id="desc">Product roadmap progress is N/A because no authoritative measurable product roadmap exists.</desc><defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop stop-color="#02050A"/><stop offset="1" stop-color="#07111C"/></linearGradient><linearGradient id="a" x1="0" y1="0" x2="1" y2="0"><stop stop-color="#0088FF"/><stop offset="1" stop-color="#62E5FF"/></linearGradient></defs><rect x="1" y="1" width="898" height="70" rx="15" fill="url(#bg)" stroke="#62E5FF" stroke-opacity=".25"/><text x="24" y="28" fill="#F4FAFF" font-family="Segoe UI,Arial,sans-serif" font-size="16" font-weight="700">Watermark Remover Pro</text><text x="24" y="49" fill="#8DA8B8" font-family="Segoe UI,Arial,sans-serif" font-size="11">Product roadmap</text><rect x="500" y="26" width="280" height="14" rx="7" fill="#08131F" stroke="#62E5FF" stroke-opacity=".16"/><path d="M512 33H768" stroke="url(#a)" stroke-width="2" stroke-dasharray="6 10" opacity=".34"/><text x="860" y="39" text-anchor="end" fill="#62E5FF" font-family="Segoe UI,Arial,sans-serif" font-size="18" font-weight="800">N/A</text></svg>'''
def valid(s,n):
    r=ET.fromstring(s)
    if r.tag.rsplit('}',1)[-1]!='svg' or 'viewBox' not in r.attrib: raise SystemExit(f'{n}: invalid SVG')
def write():
    OUT.mkdir(parents=True,exist_ok=True); (OUT/'progress-card.svg').write_text(CARD,encoding='utf-8'); (OUT/'progress-mini.svg').write_text(MINI,encoding='utf-8')
def check():
    for n,s in (('progress-card.svg',CARD),('progress-mini.svg',MINI)):
        valid(s,n); p=OUT/n
        if not p.exists() or p.read_text(encoding='utf-8')!=s: raise SystemExit(f'{n}: missing or stale')
    t=(OUT/'progress-template.svg').read_text(encoding='utf-8'); valid(t,'progress-template.svg')
    if 'TEMPLATE / NOT PROJECT DATA' not in t: raise SystemExit('template label missing')
    md=README.read_text(encoding='utf-8')
    if 'assets/readme/progress-card.svg' not in md or 'assets/readme/progress-mini.svg' not in md: raise SystemExit('README embedding missing')
    if any(p.search(md) for p in LEGACY): raise SystemExit('legacy progress meter found')
    print('OK: Watermark Remover Pro progress N/A; SVG/XML, embeddings and legacy-meter cleanup verified.')
def main():
    a=argparse.ArgumentParser(); a.add_argument('--check',action='store_true'); x=a.parse_args()
    if not x.check: write()
    check(); return 0
if __name__=='__main__': sys.exit(main())
