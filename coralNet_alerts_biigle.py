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
    df_biigle = pd.read_csv(fname_biigle)[['label_hierarchy', 'image_id', 'filename', 'shape_name', 'points',
                                           'attributes']]
    df_biigle = biigle_utils.clean_df(df=df_biigle,
                                      list_image_id=list_image_id)

    # Get Presence Absence data from BIIGLE
    df_pa_biigle = get_presence_absence_biigle(df_biigle=df_biigle,
                                               labels_of_interest=df_translation['BIIGLE'].unique().tolist())

    # CORALNET data
    df_coralNet = pd.read_csv(fname_coralnet)

    # TRANSLATION
    biigle2coral = {c: b for c, b in
                    zip(df_translation['BIIGLE'].tolist(), df_translation['CoralNet'].tolist())}

    # Init dict
    result_labels = [l for l in df_translation['BIIGLE'].unique().tolist() if '-' in l]
    dict_cell = {'cell': []}
    dict_cell.update({l: [] for l in result_labels})
    for cell in df_coralNet['cell'].unique().tolist():
        coral_cur = df_coralNet[df_coralNet['cell'] == cell]
        fname_list = coral_cur['Filename'].unique().tolist()
        biigle_cur = df_pa_biigle[df_pa_biigle['Filename'].isin(fname_list)]
        # Sum
        biigle_sum = biigle_cur.sum()
        coral_sum = coral_cur.sum()
        # Loop across labels
        for l in result_labels:
            if biigle_sum[l]:
                dict_cell[l].append(1 if coral_sum[biigle2coral[l]] else 0)
            else:
                dict_cell[l].append(np.nan)
        dict_cell['cell'].append(cell)
    df_cell = pd.DataFrame.from_dict(dict_cell)

    dict_result = {'label': [], 'TP': [], 'FN': [], 'recall': []}
    for l in result_labels:
        counts = df_cell[l].value_counts()
        if len(counts):
            tp = counts[1] if 1 in counts else 0
            fn = counts[0] if 0 in counts else 0
            dict_result['label'].append(l)
            dict_result['TP'].append(tp)
            dict_result['FN'].append(fn)
            dict_result['recall'].append(tp * 100. / (tp + fn))
    df_result = pd.DataFrame.from_dict(dict_result)

    # Save results
    df_cell.to_csv(os.path.join(ofolder, "agreement_per_cell.csv"), index=False)
    df_result.to_csv(os.path.join(ofolder, "recall_per_label.csv"), index=False)


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
    compare_coralNet_biigle_detection(fname_coralnet=args.coral_net,
                                      fname_biigle=args.biigle,
                                      fname_translation=args.t,
                                      ofolder=args.ofolder,
                                      list_image_id=list_image_id)


if __name__ == "__main__":
    main()