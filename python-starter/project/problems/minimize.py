from project.problem import Problem
import argparse
import re
import sys


class MinimizeProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument('--mini', help='az automata minimalizálása', action='store_true')

    def is_chosen_problem(self, args):
        return bool(args.mini)

    def run(self, args):
        with open(args.input, 'r', encoding='utf-8') as f:
            lines = f.read().splitlines()

        if len(lines) < 4:
            self.error('A bemeneti fájlnak legalább négy fejlécsort kell tartalmaznia.')

        states = lines[0].split()
        if not states or len(states) != len(set(states)):
            self.error('Az állapotlista üres vagy duplikált állapotot tartalmaz.')
        state_set = set(states)
        alphabet = sorted(set(lines[1].split()))
        start = lines[2].strip()
        finals = set(lines[3].split())

        if start not in state_set:
            self.error(f'Ismeretlen kezdőállapot: "{start}"')
        for state in finals - state_set:
            self.error(f'Ismeretlen végállapot: "{state}"')

        transitions = {}
        for line in lines[4:]:
            parts = line.split()
            if not parts:
                continue
            if len(parts) != 3:
                self.error(f'Hibás átmenet sor: "{line}"')
            source, symbol, target = parts
            if source not in state_set:
                self.error(f'Ismeretlen állapot: "{source}"')
            if target not in state_set:
                self.error(f'Ismeretlen állapot: "{target}"')
            if symbol not in alphabet:
                self.error(f'Ismeretlen jel: "{symbol}"')

            key = (source, symbol)
            existing_target = transitions.get(key)
            if existing_target is not None and existing_target != target:
                self.error(f'Nem determinisztikus átmenet: "{source} {symbol}"')
            transitions[key] = target

        # Use numeric q-suffixes when available so q10 is ordered after q9.
        suffixes = [re.fullmatch(r'q(\d+)', state) for state in states]
        if all(suffixes) and len({int(match.group(1)) for match in suffixes}) == len(states):
            rank = {state: int(match.group(1)) for state, match in zip(states, suffixes)}
        else:
            rank = {state: index for index, state in enumerate(states)}
        ordered_states = sorted(states, key=rank.__getitem__)

        # Unreachable states cannot affect the language recognized by the DFA.
        reachable = {start}
        pending = [start]
        while pending:
            source = pending.pop()
            for symbol in alphabet:
                target = transitions.get((source, symbol))
                if target is not None and target not in reachable:
                    reachable.add(target)
                    pending.append(target)
        ordered_reachable = [state for state in ordered_states if state in reachable]

        # A virtual rejecting sink gives missing transitions their DFA semantics.
        sink = object()
        universe = ordered_reachable + [sink]
        blocks = [
            [state for state in universe if (state in finals) == is_final]
            for is_final in (False, True)
        ]
        blocks = [block for block in blocks if block]

        while True:
            block_index = {
                state: index
                for index, block in enumerate(blocks)
                for state in block
            }
            refined = []
            signatures = {}
            for state in universe:
                is_final = state in finals
                destinations = []
                for symbol in alphabet:
                    if state is sink:
                        target = sink
                    else:
                        target = transitions.get((state, symbol), sink)
                    destinations.append(block_index[target])
                signature = (is_final, tuple(destinations))
                if signature not in signatures:
                    signatures[signature] = []
                    refined.append(signatures[signature])
                signatures[signature].append(state)
            if len(refined) == len(blocks):
                blocks = refined
                break
            blocks = refined

        minimized_class = {
            state: index
            for index, block in enumerate(blocks)
            for state in block
        }
        members = {
            index: [state for state in block if state is not sink]
            for index, block in enumerate(blocks)
        }
        class_name = {
            index: f's{min(rank[state] for state in states_in_class)}'
            for index, states_in_class in members.items()
            if states_in_class
        }
        output_classes = sorted(
            class_name,
            key=lambda index: min(rank[state] for state in members[index]),
        )

        out = [
            ' '.join(class_name[index] for index in output_classes),
            ' '.join(alphabet),
            class_name[minimized_class[start]],
            ' '.join(
                class_name[index]
                for index in output_classes
                if any(state in finals for state in members[index])
            ),
        ]

        output_transitions = set()
        for state in ordered_reachable:
            source_class = minimized_class[state]
            for symbol in alphabet:
                target = transitions.get((state, symbol))
                if target is None:
                    continue
                target_class = minimized_class[target]
                output_transitions.add(
                    (source_class, symbol, target_class)
                )

        def transition_key(transition):
            source_class, symbol, target_class = transition
            return (
                min(rank[state] for state in members[source_class]),
                symbol,
                min(rank[state] for state in members[target_class]),
            )

        for source_class, symbol, target_class in sorted(
            output_transitions, key=transition_key
        ):
            out.append(
                f'{class_name[source_class]} {symbol} {class_name[target_class]}'
            )

        with open(args.output, 'w', encoding='utf-8') as f:
            f.write('\n'.join(out))

    @staticmethod
    def error(message):
        print(message, file=sys.stderr)
        sys.exit(1)
