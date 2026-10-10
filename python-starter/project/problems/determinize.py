from project.problem import Problem
import argparse
import sys


class DeterminizeProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        A --det kapcsoló értéket nem vár, csak jelzi a determinizálást
        """
        parser.add_argument('--det', help='az automata determinizálása', action='store_true')

    def is_chosen_problem(self, args):
        """
        Akkor ez a feladat fut, ha meg van adva a --det
        """
        return bool(args.det)

    def run(self, args):
        with open(args.input, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()

        # Fejléc (a végállapot-sor lehet üres, ezért nem szűrjük a sorokat)
        states = set(lines[0].split())
        alphabet = sorted(set(lines[1].split()))
        start = lines[2].strip()
        finals = set(lines[3].split())

        # Átmenetek beolvasása hibaellenőrzéssel
        # (állapot, szimbólum) -> célállapotok halmaza
        nfa = {}
        for line in lines[4:]:
            parts = line.split()
            if not parts:
                continue
            if len(parts) != 3:
                self.error(f'Hibás átmenet sor: "{line}"')
            source, symbol, target = parts
            if source not in states:
                self.error(f'Ismeretlen állapot: "{source}"')
            if target not in states:
                self.error(f'Ismeretlen állapot: "{target}"')
            if symbol not in alphabet:
                self.error(f'Ismeretlen jel: "{symbol}"')
            nfa.setdefault((source, symbol), set()).add(target)

        # Részhalmaz-konstrukció, szélességi bejárással
        # order: a felfedezett DFA állapotok (NFA állapothalmazok) sorrendben
        # index: halmaz -> az s-szám (s0, s1, ...)
        start_set = frozenset([start])
        order = [start_set]
        index = {start_set: 0}
        transitions = []

        i = 0
        while i < len(order):
            current = order[i]
            for symbol in alphabet:
                target = set()
                for state in current:
                    target |= nfa.get((state, symbol), set())
                if not target:
                    continue  # nincs átmenet, nem soroljuk fel
                target = frozenset(target)
                if target not in index:
                    index[target] = len(order)
                    order.append(target)
                transitions.append((i, symbol, index[target]))
            i += 1

        # Kimenet összeállítása
        out = []
        out.append(' '.join(f's{n}' for n in range(len(order))))
        out.append(' '.join(alphabet))
        out.append('s0')
        out.append(' '.join(f's{n}' for n, group in enumerate(order) if group & finals))
        for source, symbol, target in transitions:
            out.append(f's{source} {symbol} s{target}')

        with open(args.output, 'w', encoding='utf-8') as f:
            f.write('\n'.join(out))

    @staticmethod
    def error(message):
        """
        Hibaüzenet a hibakimenetre, a program leáll
        """
        print(message, file=sys.stderr)
        sys.exit(1)