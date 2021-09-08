import os
import zipfile
import shutil
import argparse
import requests
import pandas as pd
from tqdm import tqdm
from biigle.biigle import Api


# Example:
#   python merge_biigle_reports.py -i C:\Users\cgros\Downloads\292_csv_image_annotation_report(1) -t 839-vme-morpho-taxa.csv -a C:\Users\cgros\data\image_area -o 20210908_biigle_vme.csv


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')
    mandatory_args.add_argument('-i', '--ifolder', required=True, type=str,
                                help='Input folder containing zip archives for each survey.')
    mandatory_args.add_argument('-t', '--ifname', required=True, type=str,
                                help='Input filename in each zip archives.')
    mandatory_args.add_argument('-o', '--ofname', required=True, type=str,
                                help='CSV filename output.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')

    return parser


def merge_biigle_reports(folder_i, fname_i, fname_o):
    # Loop across archived folders
    lst_df = []
    for survey_zip in os.listdir(folder_i):
        if survey_zip.endswith(".zip"):
            path_zip = os.path.join(folder_i, survey_zip)
            archive = zipfile.ZipFile(path_zip, 'r')
            try:
                df = pd.read_csv(archive.open(fname_i))
                print("Found {} annotations in {}...".format(len(df), survey_zip))
                lst_df.append(df)
            except:
                print("No annotation found in {}...".format(survey_zip))

    df_stacked = pd.concat(lst_df, axis=0)

    print("\nTotal number of annotations: {}...".format(len(df_stacked)))
    print("Saving result in: {}...".format(fname_o))
    df_stacked.to_csv(fname_o, index=False)


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    merge_biigle_reports(folder_i=args.ifolder, fname_i=args.ifname, fname_o=args.ofname)


if __name__ == "__main__":
    main()
