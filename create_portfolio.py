import os
import argparse
import numpy as np
import pandas as pd


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')
    mandatory_args.add_argument('-i', '--input-folder', required=True, type=str,
                                help='Database folder.')
    mandatory_args.add_argument('-c', '--coral-net', required=True, type=str,
                                help='CoralNet folder suffix.')
    mandatory_args.add_argument('-b', '--biigle', required=True, type=str,
                                help='BIIGLE folder suffix.')
    mandatory_args.add_argument('-o', '--ofolder', required=True, type=str,
                                help='Output folder. Created if does not exist yet.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')
    optional_args.add_argument('-t', required=False, type=str, default='coralnet_to_biigle.csv',
                                help='CoralNet to BIIGLE label translation table.')
    optional_args.add_argument('-n', required=False, type=str, default=10,
                                help='Number of patches per label.')
    return parser


def create_portfolio(input_folder, suffix_coralnet, suffix_biigle, n_samples, fname_translation, ofolder):
    # Create ofolder if does not exist yet
    if not os.path.isdir(ofolder):
        os.makedirs(ofolder)

    # Translation table between CoralNet and BIIGLE
    df_translation = pd.read_csv(fname_translation)


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    create_portfolio(input_folder=args.input_folder,
                     suffix_coralnet=args.coral_net,
                     suffix_biigle=args.biigle,
                     n_samples=args.n,
                     fname_translation=args.t,
                     ofolder=args.ofolder)


if __name__ == "__main__":
    main()