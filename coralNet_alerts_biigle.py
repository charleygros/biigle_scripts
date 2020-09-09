import os
import argparse
import numpy as np
import pandas as pd

import utils as biigle_utils


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')
    mandatory_args.add_argument('-c', '--coral-net', required=True, type=str,
                                help='CoralNet csv file.')
    mandatory_args.add_argument('-b', '--biigle', required=True, type=str,
                                help='BIIGLE csv file.')
    mandatory_args.add_argument('-o', '--ofolder', required=True, type=str,
                                help='Output folder. Created if does not exist yet.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')
    optional_args.add_argument('-t', required=False, type=str, default='coralnet_to_biigle.csv',
                                help='CoralNet to BIIGLE label translation table.')
    optional_args.add_argument('-i', '--image-id', required=False, type=str,
                                help='Image ID of interest. If multiple, separate them with commas. If range, separate '
                                     'limits with dash.')
    return parser


def get_presence_absence_biigle(df_biigle, labels_of_interest):
    # Init empty dict
    df_biigle_detection = pd.DataFrame(columns=['Filename'] + labels_of_interest)
    # Loop across images
    for n_ii, ii in enumerate(df_biigle['filename'].unique().tolist()):
        # init dict
        dict_cur = {l: 0 for l in labels_of_interest}
        dict_cur['Filename'] = ii
        # Select rows
        df_cur = df_biigle[df_biigle['filename'] == ii]
        # Get labels
        labels_cur = df_cur['label_hierarchy'].unique().tolist()
        dict_update = {l: 1 for l in labels_cur}
        # Update dict
        dict_cur.update(dict_update)
        # Add row to df_biigle_detection
        df_biigle_detection = pd.concat([df_biigle_detection, pd.DataFrame(dict_cur, index=[n_ii])])

    return df_biigle_detection


def coralNet_alerts_biigle(fname_coralnet, fname_biigle, fname_translation, ofolder, list_image_id=None):
    # Create ofolder if does not exist yet
    if not os.path.isdir(ofolder):
        os.makedirs(ofolder)

    # DF translation
    df_translation = pd.read_csv(fname_translation)

    # BIIGLE data
    df_biigle = pd.read_csv(fname_biigle)
    df_biigle = biigle_utils.clean_df(df=df_biigle,
                                      list_image_id=list_image_id)

    # Get Presence Absence data from BIIGLE
    df_pa_biigle = get_presence_absence_biigle(df_biigle=df_biigle,
                                               labels_of_interest=df_translation['BIIGLE'].unique().tolist())

    # CORALNET data
    df_coralNet = pd.read_csv(fname_coralnet)

    # TRANSLATION
    coralNet2biigle = {c: b for c, b in zip(df_translation['CoralNet'].tolist(), df_translation['BIIGLE'].tolist())}

    # Loop through images
    for f in df_biigle['filename'].unique().tolist():
        print('\nf')
        # Current data
        df_coralNet_f = df_coralNet[df_coralNet["Name"] == f]
        df_biigle_f = df_biigle[df_biigle["filename"] == f]
        # CoralNet Labels
        labels_coralNet = df_coralNet_f["Label"].unique().tolist()
        # Only CoralNet Labels of interest
        labels_coralNet = [l for l in labels_coralNet if l in df_translation['CoralNet'].tolist()]
        # BIIGLE Labels
        labels_biigle = df_biigle_f["label_hierarchy"].unique().tolist()
        # Check False Negative
        labels_false_negative = [l for l in labels_coralNet if coralNet2biigle[l] not in labels_biigle]
        # Print alerts
        if len(labels_false_negative):
            print('\nf')
            print('\n\t'.join(labels_false_negative))


def main():
    parser = get_parser()
    args = parser.parse_args()

    if args.image_id:
        if ',' in args.image_id:
            list_image_id = args.image_id.split(',')
        elif '-' in args.image_id:
            limits = args.image_id.split('-')
            list_image_id = range(int(limits[0]), int(limits[1]))
        else:
            list_image_id = [args.image_id]
    else:
        list_image_id = None

    # Run function
    coralNet_alerts_biigle(fname_coralnet=args.coral_net,
                           fname_biigle=args.biigle,
                           fname_translation=args.t,
                           ofolder=args.ofolder,
                           list_image_id=list_image_id)


if __name__ == "__main__":
    main()
