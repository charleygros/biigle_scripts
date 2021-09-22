import os
import pandas as pd
import argparse

# python concat_image_quality_surveys.py -i R:\IMAS\Antarctic_Seafloor\image_quality_analysis


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')
    mandatory_args.add_argument('-i', '--ifolder', required=True, type=str,
                                help='Input folder containing all surveys.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-r', '--rm', dest='rm', required=False, type=bool, default=False,
                               help='If False, only surveys with no existing results will be processed. If True, all'
                                    ' surveys will be processed.')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')

    return parser


def concat_image_quality_surveys(input_folder):
    lst_df = []
    for f in os.listdir(input_folder):
        if f.endswith(".csv") and f.startswith("results_"):
            df = pd.read_csv(os.path.join(input_folder, f))
            lst_df.append(df)

    df_full = pd.concat(lst_df)
    print(len(df_full))
    fname_out = os.path.join(input_folder, "image_quality_score.csv")
    df_full.to_csv(fname_out, index=False)


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    concat_image_quality_surveys(input_folder=args.ifolder)


if __name__ == "__main__":
    main()
