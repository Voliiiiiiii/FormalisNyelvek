import argparse

class Problem(object):

    def __init__(self):
        pass

    def initialize_parser(self, parser: argparse.ArgumentParser):
        """
        Initialize the parser with the necessary arguments
        """
        raise NotImplementedError
    
    def is_chosen_problem(self, args):
        """
        Check if the problem is chosen
        """
        raise NotImplementedError

    def run(self, args):
        """
        Run the problem
        """
        raise NotImplementedError


#BASE CLASS DEFINES THEREE METHODS