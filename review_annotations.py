import os
import shutil
import argparse
import requests
from tqdm import tqdm
from biigle.biigle import Api


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')
    mandatory_args.add_argument('-e', '--email', required=True, type=str,
                                help='Email address used for BIIGLE account.')
    mandatory_args.add_argument('-t', '--token', required=True, type=str,
                                help='BIIGLE API token. To generate one: https://biigle.de/settings/tokens')
    mandatory_args.add_argument('-o', '--ifolder', required=True, type=str,
                                help='Input folder, filled with "pull_patches".')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')

    return parser


def review_annotations(email, token, ifolder):
    pass


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    review_annotations(email=args.email,
                       token=args.token,
                       input_folder=args.ifolder)


if __name__ == "__main__":
    main()