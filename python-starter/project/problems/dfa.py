from project.problem import Problem
import argparse


class DfaProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        A --check kapcsoló a vesszővel elválasztott szavakat várja
        """
        parser.add_argument('--check', help='ellenőrizendő szavak, vesszővel elválasztva')

    def is_chosen_problem(self, args):
        """
        Akkor ez a feladat fut, ha meg van adva a --check
        """
        return args.check is not None

    def run(self, args):
        with open(args.input, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()

        # Fejléc: az első 4 sort nem szűrjük, mert a végállapot-sor lehet üres
        # states = lines[0].split()  # nincs rá szükségünk
        # alphabet = lines[1].split()  # nincs rá szükségünk
        start = lines[2].strip()
        accepting = set(lines[3].split())

        # Átmenetek: (állapot, szimbólum) -> új állapot
        transitions = {}
        for line in lines[4:]:
            parts = line.split()
            if len(parts) == 3:
                source, symbol, target = parts
                transitions[(source, symbol)] = target

        results = []
        for word in args.check.split(','):
            results.append('IGEN' if self.accepts(word, start, accepting, transitions) else 'NEM')

        with open(args.output, 'w', encoding='utf-8') as f:
            f.write('\n'.join(results))

    @staticmethod
    def accepts(word, start, accepting, transitions):
        """
        Végigmegy a szón; ha hiányzik az átmenet, a szót elutasítja
        """
        state = start
        for symbol in word:
            state = transitions.get((state, symbol))
            if state is None:
                return False
        return state in accepting