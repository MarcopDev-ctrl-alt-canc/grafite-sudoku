"""Motore sudoku (classico / X / jigsaw): generazione, unicità, verifica con 'singles'."""
import random

N = 9
ALL = (1 << 9) - 1


def box_of(i):
    r, c = divmod(i, 9)
    return (r // 3) * 3 + c // 3


def units_for(variant, regions=None):
    units = []
    for r in range(9):
        units.append([r * 9 + c for c in range(9)])
    for c in range(9):
        units.append([r * 9 + c for r in range(9)])
    if variant == "jigsaw":
        for k in range(9):
            units.append([i for i in range(81) if regions[i] == k])
    else:
        for b in range(9):
            units.append([i for i in range(81) if box_of(i) == b])
    if variant == "x":
        units.append([i * 9 + i for i in range(9)])
        units.append([i * 9 + (8 - i) for i in range(9)])
    return units


def peers_from(units):
    peers = [set() for _ in range(81)]
    for u in units:
        for a in u:
            for b in u:
                if a != b:
                    peers[a].add(b)
    return [sorted(p) for p in peers]


def candidates(grid, peers):
    cands = [0] * 81
    for i in range(81):
        if grid[i]:
            continue
        used = 0
        for p in peers[i]:
            if grid[p]:
                used |= 1 << (grid[p] - 1)
        cands[i] = ALL & ~used
    return cands


def count_solutions(grid, peers, limit=2):
    grid = grid[:]
    count = 0

    def rec():
        nonlocal count
        best, bestc = -1, 10
        cands = candidates(grid, peers)
        for i in range(81):
            if grid[i] == 0:
                n = bin(cands[i]).count("1")
                if n == 0:
                    return
                if n < bestc:
                    best, bestc = i, n
                    if n == 1:
                        break
        if best == -1:
            count += 1
            return
        m = cands[best]
        for d in range(9):
            if m & (1 << d):
                grid[best] = d + 1
                rec()
                grid[best] = 0
                if count >= limit:
                    return

    rec()
    return count


def random_full(peers):
    grid = [0] * 81

    def rec():
        cands = candidates(grid, peers)
        best, bestc = -1, 10
        for i in range(81):
            if grid[i] == 0:
                n = bin(cands[i]).count("1")
                if n == 0:
                    return False
                if n < bestc:
                    best, bestc = i, n
        if best == -1:
            return True
        digs = [d for d in range(9) if cands[best] & (1 << d)]
        random.shuffle(digs)
        for d in digs:
            grid[best] = d + 1
            if rec():
                return True
            grid[best] = 0
        return False

    ok = rec()
    return grid if ok else None


def singles_solvable(puzzle, units, peers):
    """True se si risolve solo con naked + hidden singles."""
    grid = puzzle[:]
    while True:
        if all(grid):
            return True
        cands = candidates(grid, peers)
        progress = False
        for i in range(81):
            if grid[i] == 0 and bin(cands[i]).count("1") == 1:
                grid[i] = cands[i].bit_length()
                progress = True
                cands = candidates(grid, peers)
        if progress:
            continue
        for u in units:
            for d in range(9):
                bit = 1 << d
                spots = [i for i in u if grid[i] == 0 and cands[i] & bit]
                if any(grid[i] == d + 1 for i in u):
                    continue
                if len(spots) == 1:
                    grid[spots[0]] = d + 1
                    progress = True
                    cands = candidates(grid, peers)
        if not progress:
            return False


def carve(solution, peers, target_clues):
    puzzle = solution[:]
    pairs = []
    seen = set()
    for i in range(81):
        j = 80 - i
        if i not in seen and j not in seen:
            pairs.append((i, j))
            seen.add(i)
            seen.add(j)
    random.shuffle(pairs)
    clues = 81
    for i, j in pairs:
        if clues <= target_clues:
            break
        a, b = puzzle[i], puzzle[j]
        puzzle[i] = 0
        puzzle[j] = 0
        if count_solutions(puzzle, peers, 2) != 1:
            puzzle[i], puzzle[j] = a, b
        else:
            clues -= 2 if i != j else 1
    return puzzle


def connected(cells):
    cells = set(cells)
    start = next(iter(cells))
    stack, seen = [start], {start}
    while stack:
        x = stack.pop()
        r, c = divmod(x, 9)
        for rr, cc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
            if 0 <= rr < 9 and 0 <= cc < 9:
                y = rr * 9 + cc
                if y in cells and y not in seen:
                    seen.add(y)
                    stack.append(y)
    return len(seen) == len(cells)


def make_regions(solution, swaps=6000):
    regions = [box_of(i) for i in range(81)]
    for _ in range(swaps):
        a = random.randrange(81)
        r, c = divmod(a, 9)
        nbrs = [(r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)]
        nbrs = [rr * 9 + cc for rr, cc in nbrs if 0 <= rr < 9 and 0 <= cc < 9]
        nbrs = [x for x in nbrs if regions[x] != regions[a]]
        if not nbrs:
            continue
        r2 = regions[random.choice(nbrs)]
        cands = [b for b in range(81) if regions[b] == r2 and solution[b] == solution[a]]
        if not cands:
            continue
        b = random.choice(cands)
        r1 = regions[a]
        regions[a], regions[b] = r2, r1
        ok = connected([i for i in range(81) if regions[i] == r1]) and connected(
            [i for i in range(81) if regions[i] == r2]
        )
        if not ok:
            regions[a], regions[b] = r1, r2
    return regions


def region_irregularity(regions):
    """Quante celle non stanno più nel proprio box 3x3 (più alto = forme più 'jigsaw')."""
    return sum(1 for i in range(81) if regions[i] != box_of(i))


def validate(solution, units):
    for u in units:
        if sorted(solution[i] for i in u) != list(range(1, 10)):
            return False
    return True


def generate(variant, target_clues, want_singles=None, seed=None, tries=400):
    if seed is not None:
        random.seed(seed)
    for _ in range(tries):
        regions = None
        if variant == "jigsaw":
            base_units = units_for("classic")
            base_peers = peers_from(base_units)
            sol0 = random_full(base_peers)
            regions = make_regions(sol0)
            if region_irregularity(regions) < 28:
                continue
            units = units_for("jigsaw", regions)
            peers = peers_from(units)
            sol = sol0
        else:
            units = units_for(variant)
            peers = peers_from(units)
            sol = random_full(peers)
        if not validate(sol, units):
            continue
        puz = carve(sol, peers, target_clues)
        clues = sum(1 for v in puz if v)
        if count_solutions(puz, peers, 2) != 1:
            continue
        sing = singles_solvable(puz, units, peers)
        if want_singles is True and not sing:
            continue
        if want_singles is False and sing:
            continue
        if clues > target_clues + 3:
            continue
        return {
            "variant": variant,
            "puzzle": puz,
            "solution": sol,
            "regions": regions,
            "clues": clues,
            "singles_only": sing,
        }
    raise RuntimeError("generazione fallita per " + variant)
