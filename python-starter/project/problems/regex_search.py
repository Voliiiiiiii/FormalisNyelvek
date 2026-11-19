from project.problem import Problem
import argparse
import re
from collections import Counter


DATE = r'[0-9-]+'
TIME = r'[0-9:.]+'
PID = r'[0-9]+'
TID = r'[0-9]+'
# A tag tartalmazhat ':'-ot (pl. "niss:interactor", "APM::AudioPolicyEngine/Base"),
# a tag végét az első ": " (vagy a sor végi ':') jelzi.
TAG_CHAR = r'(?:[^:\r\n]|:(?=[^ \r\n]))'
TAG = rf'{TAG_CHAR}+'
MESSAGE = r'[^\r\n]*'

LOG_RECORD_RE = re.compile(
    rf'^{DATE} {TIME} +(?P<pid>{PID}) +(?P<tid>{TID}) '
    rf'(?P<priority>[IDVEFAW]) (?P<tag>{TAG}):'
    rf'(?: (?P<message>{MESSAGE}))?$',
    re.MULTILINE,
)
ERROR_RECORD_RE = re.compile(
    rf'^{DATE} {TIME} +(?P<pid>{PID}) +{TID} E {TAG}:'
    rf'(?: (?P<message>{MESSAGE}))?$',
    re.MULTILINE,
)
MAIN_THREAD_ERROR_RE = re.compile(
    rf'^{DATE} {TIME} +(?P<pid>{PID}) +(?P=pid) E {TAG}:'
    rf'(?: {MESSAGE})?$',
    re.MULTILINE,
)
JAVA_SOURCE_RE = re.compile(r'\b([A-Za-z_$][\w$]*\.java):\d+\b')


class RegexSearchProblem(Problem):

    def initialize_parser(self, parser: argparse.ArgumentParser):
        parser.add_argument(
            '--rgx',
            type=int,
            choices=range(1, 6),
            help='a megoldandó regexes feladat sorszáma (1-5)',
        )

    def is_chosen_problem(self, args):
        return args.rgx is not None

    def run(self, args):
        with open(args.input, 'r', encoding='utf-8') as input_file:
            log_text = input_file.read()

        if args.rgx == 1:
            results = self.count_requested_lines(log_text)
        elif args.rgx == 2:
            results = self.java_sources(log_text)
        elif args.rgx == 3:
            results = self.process_ids(log_text)
        elif args.rgx == 4:
            results = self.process_with_most_errors(log_text)
        else:
            results = [str(len(MAIN_THREAD_ERROR_RE.findall(log_text)))]

        with open(args.output, 'w', encoding='utf-8') as output_file:
            output_file.write('\n'.join(results))

    @staticmethod
    def count_requested_lines(log_text):
        patterns = (
            rf'^10-15 {TIME} +{PID} +{TID} [IDVEFAW] {TAG}:(?: {MESSAGE})?$',
            rf'^10-15 10:18:51(?:\.[0-9]+)? +{PID} +{TID} '
            rf'[IDVEFAW] {TAG}:(?: {MESSAGE})?$',
            rf'^{DATE} [0-9]{{2}}:[0-9]{{2}}:51(?:\.[0-9]+)? '
            rf'+{PID} +{TID} [IDVEFAW] {TAG}:(?: {MESSAGE})?$',
            rf'^{DATE} {TIME} +{PID} +{TID} [IDVEFAW] '
            rf'{TAG_CHAR}*lowmemorykiller{TAG_CHAR}*:(?: {MESSAGE})?$',
            rf'^{DATE} 10:18:51(?:\.[0-9]+)? +221 +{TID} '
            rf'[IDVEFAW] {TAG}:(?: {MESSAGE})?$',
            rf'^{DATE} {TIME} +{PID} +{TID} E {TAG}:(?: {MESSAGE})?$',
            rf'^{DATE} {TIME} +{PID} +{TID} W PackageManager:'
            rf'(?: {MESSAGE})?$',
            rf'^{DATE} {TIME} +{PID} +{TID} D '
            rf'{TAG_CHAR}*ExoPlayer{TAG_CHAR}*:(?: {MESSAGE})?$',
            rf'^{DATE} {TIME} +{PID} +{TID} [EW] {TAG}:'
            rf'(?=[^\r\n]*\.java:)(?: {MESSAGE})?$',
            rf'^{DATE} {TIME} +{PID} +{TID} [IDVEFAW] {TAG}: '
            rf'(?=[^\r\n]*\bThread\b){MESSAGE}$',
        )
        return [str(len(re.findall(pattern, log_text, re.MULTILINE))) for pattern in patterns]

    @staticmethod
    def java_sources(log_text):
        sources = []
        for error in ERROR_RECORD_RE.finditer(log_text):
            message = error.group('message') or ''
            sources.extend(match.group(1) for match in JAVA_SOURCE_RE.finditer(message))
        return sources

    @staticmethod
    def process_ids(log_text):
        process_ids = dict.fromkeys(
            match.group('pid') for match in LOG_RECORD_RE.finditer(log_text)
        )
        return list(process_ids)

    @staticmethod
    def process_with_most_errors(log_text):
        error_counts = Counter(
            match.group('pid') for match in ERROR_RECORD_RE.finditer(log_text)
        )
        if not error_counts:
            return []

        process_id, count = error_counts.most_common(1)[0]
        return [f'PID={process_id} ({count} errors)']
