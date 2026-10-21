"""Genera data/puzzles.json: gli schemi delle pagine da stampare.

    python tools/make_puzzles.py

I 5 schemi della serie 3 (data/serie3.json, già su Pinterest) restano identici
e in testa alla loro categoria; gli altri si generano con seed fissi, quindi
rilanciare lo script dà sempre lo stesso file. Per aggiungere schemi si
allunga PLAN (nuove righe in fondo alla categoria): i vecchi non cambiano.

Livelli, con il motore in sudoku_engine.py:
- easy: si risolve solo con i singoli (naked e hidden single);
- medium e hard: servono tecniche oltre i singoli; hard ha meno indizi.
È una stima, non una misura vera della difficoltà.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import sudoku_engine as eng  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# categoria: (variante, livello, indizi, solo singoli?)
CATEGORIES = {
    'easy': ('classic', 'easy', 36, True),
    'medium': ('classic', 'medium', 30, False),
    'hard': ('classic', 'hard', 25, False),
    'large-print': ('classic', 'easy', 38, True),
    'x': ('x', None, None, None),
    'jigsaw': ('jigsaw', None, None, None),
}
LEVEL_PARAMS = {'easy': (32, True), 'medium': (29, False)}

# Ordine delle pagine: (categoria, slug della serie 3 oppure livello per le varianti).
PLAN = {
    'easy': ['quick-easy-sudoku', None, None, None],
    'medium': [None, None, None, None],
    'hard': ['hard-sudoku-challenge', None, None, None],
    'large-print': ['large-print-sudoku-easy', None, None, None],
    'x': ['easy', 'easy', 'x-sudoku-medium', 'medium'],
    'jigsaw': ['jigsaw-sudoku-easy', 'easy', 'medium', 'medium'],
}


def main():
    serie3 = {p['slug']: p for p in json.load(open(os.path.join(ROOT, 'data', 'serie3.json'), encoding='utf-8'))}
    out = []
    for cat, slots in PLAN.items():
        variant, level, clues, singles = CATEGORIES[cat]
        for n, slot in enumerate(slots, start=1):
            if slot in serie3:
                p = serie3[slot]
                lvl = p['level'].lower()
                entry = dict(variant=p['variant'], level=lvl, clues=p['clues'], puzzle=p['puzzle'],
                             solution=p['solution'], regions=p['regions'], singles_only=p['singles_only'],
                             serie3_slug=slot)
            else:
                lvl = level or slot
                c, s = (clues, singles) if level else LEVEL_PARAMS[lvl]
                seed = f'{cat}-{n}'
                g = eng.generate(variant, c, want_singles=s, seed=seed, tries=2000)
                entry = dict(variant=variant, level=lvl, clues=g['clues'], puzzle=g['puzzle'],
                             solution=g['solution'], regions=g['regions'], singles_only=g['singles_only'])
                print(f'{cat} #{n}: {lvl}, {g["clues"]} indizi, solo singoli: {g["singles_only"]}', flush=True)
            entry.update(category=cat, number=n)
            out.append(entry)
    for p in out:
        check(p)
    path = os.path.join(ROOT, 'data', 'puzzles.json')
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(out, f, ensure_ascii=False, separators=(',', ':'))
        f.write('\n')
    print(f'{len(out)} schemi in {path}')


def check(p):
    """Soluzione valida, coerente con gli indizi, unica."""
    units = eng.units_for(p['variant'], p['regions'])
    peers = eng.peers_from(units)
    assert eng.validate(p['solution'], units), p
    assert all(v == 0 or v == s for v, s in zip(p['puzzle'], p['solution'])), p
    assert eng.count_solutions(p['puzzle'], peers, 2) == 1, p
    assert eng.singles_solvable(p['puzzle'], units, peers) == p['singles_only'], p


if __name__ == '__main__':
    main()
