import os
import argparse
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

sns.set(style="whitegrid")

CORALNET_UNSCORABLE = ["NoID", "NoID_ExpOp", "NoID_TBD", "Unscorable"]


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
                                help='Image ID of interest. If multiple, separate them with commas.')
    return parser


def compute_coralNet_abundance(data, labels_of_interest, unscorable_labels, images_of_interest):
    dict_out = {l: [] for l in labels_of_interest}
    dict_out["im"] = []

    # Loop across images
    for im in images_of_interest:
        dict_out['im'].append(im)
        df_im = data[data["Name"] == im]
        # Count unscorable
        cmpt_unscorable = len(df_im[df_im.Label.isin(unscorable_labels)])
        # Count number of labels
        cmpt_tot = len(df_im)
        # Loop across labels of interest
        for label in labels_of_interest:
            cmpt = len(df_im[df_im.Label == label])
            dict_out[label].append(float(cmpt) * 100. / (cmpt_tot - cmpt_unscorable))

    return pd.DataFrame.from_dict(dict_out)


def PolyArea(x,y):
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))


def compute_biigle_abundance(data, labels_of_interest, images_of_interest):
    dict_out = {l: [] for l in labels_of_interest}
    dict_out["im"] = []

    # Loop across images
    for im in images_of_interest:
        dict_out['im'].append(im)
        df_im = data[data["filename"] == im]
        # Get image attributes
        height = float(df_im.iloc[0, :]["attributes"].split('"height":')[-1].split(',')[0])
        width = float(df_im.iloc[0, :]["attributes"].split('"width":')[-1].split(',')[0])
        # Loop across labels of interest
        for label in labels_of_interest:
            df_im_label = df_im[df_im['label_hierarchy'] == label]
            area = 0
            for index, row in df_im_label.iterrows():
                if row['shape_name'] == "Circle":
                    radius = float(row['points'].split(',')[2].split(']')[0])
                    area += np.pi * radius * radius
                elif row['shape_name'] in ['Rectangle', 'LineString', 'Polygon']:
                    coords = [float(c) for c in row['points'].split('[')[-1].split(']')[0].split(',')]
                    x, y = coords[0::2], coords[1::2]
                    area += PolyArea(x, y)
                elif row['shape_name'] == 'Point':
                    pass
                else:
                    print(row)
                    exit()
            # Compute abundance
            dict_out[label].append(float(area) * 100. / (height * width))

    return pd.DataFrame.from_dict(dict_out)


def convert_naming(data, table, dest, src):
    for label_dest in table[dest].unique().tolist():
        label_src = table[table[dest] == label_dest][src].tolist()
        data[label_dest] = data[label_src].sum(axis=1)
    return data[["im"] + table[dest].unique().tolist()]


def sum_families(data, families):
    list_families = [f for f in families if not '-' in f]
    for fam in list_families:
        data[fam] = data[[f for f in families if f.startswith(fam)]].sum(axis=1)
    return data


def compare_coralNet_biigle_abundance(fname_coralnet, fname_biigle, fname_translation, ofolder, list_image_id=None):
    # Create ofolder if does not exist yet
    if not os.path.isdir(ofolder):
        os.makedirs(ofolder)

    # CoralNet data
    df_coralNet = pd.read_csv(fname_coralnet)[['Name', 'Label']]

    # BIIGLE data
    df_biigle = pd.read_csv(fname_biigle)[['label_hierarchy', 'image_id', 'filename', 'shape_name', 'points',
                                           'attributes']]
    df_biigle['label_hierarchy'] = df_biigle['label_hierarchy'].str.replace(' > ', '-')
    df_biigle['label_hierarchy'] = df_biigle['label_hierarchy'].str.replace(' ', '_')

    # Get image filenames of interest
    if list_image_id:
        list_image_fname = df_biigle[df_biigle['image_id'].isin(list_image_id)]['filename'].unique().tolist()
    else:
        list_image_fname = df_biigle['filename'].unique().tolist()
    print('\n{} images selected.'.format(len(list_image_fname)))

    # Translation table between CoralNet and BIIGLE
    df_translation = pd.read_csv(fname_translation)

    # Compute CoralNet Abundance
    df_coralNet_abundance = compute_coralNet_abundance(data=df_coralNet,
                                                       labels_of_interest=df_translation['CoralNet'].unique().tolist(),
                                                       unscorable_labels=CORALNET_UNSCORABLE,
                                                       images_of_interest=list_image_fname)
    # Move from CoralNet to BIIGLE naming
    df_coralNet_abundance = convert_naming(data=df_coralNet_abundance,
                                           table=df_translation,
                                           dest='BIIGLE',
                                           src='CoralNet')

    # Compute BIIGLE Abundance
    df_biigle_abundance = compute_biigle_abundance(data=df_biigle,
                                                   labels_of_interest=df_translation['BIIGLE'].unique().tolist(),
                                                   images_of_interest=list_image_fname)

    # Sum big families
    df_biigle_abundance = sum_families(data=df_biigle_abundance,
                                        families=df_translation['BIIGLE'].unique().tolist())
    df_coralNet_abundance = sum_families(data=df_coralNet_abundance,
                                         families=df_translation['BIIGLE'].unique().tolist())

    # Violin plots
    for label in df_translation['BIIGLE'].unique().tolist():
        vals_biigle = df_biigle_abundance[label].tolist()
        vals_coralNet = df_coralNet_abundance[label].tolist()
        if sum(vals_coralNet) or sum(vals_biigle):
            fname_out = os.path.join(ofolder, label+'.png')
            df_plot = pd.DataFrame.from_dict({'CoralNet': vals_coralNet, 'BIIGLE': vals_biigle})
            plt.figure(figsize=(5, 10))
            sns.catplot(data=df_plot, order=["CoralNet", "BIIGLE"], palette="Set2", jitter=True)
            plt.ylabel('Abundance per image [%]')
            plt.title(label)
            plt.ylim(0)
            plt.savefig(fname_out)
            plt.close()


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    compare_coralNet_biigle_abundance(fname_coralnet=args.coral_net,
                                      fname_biigle=args.biigle,
                                      fname_translation=args.t,
                                      ofolder=args.ofolder,
                                      list_image_id=args.image_id.split(',') if args.image_id else None)


if __name__ == "__main__":
    main()