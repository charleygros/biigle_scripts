import os
import shutil
import argparse
import random
import pandas as pd


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')
    mandatory_args.add_argument('-i', '--input-folder', required=True, type=str,
                                help='Database folder.')
    mandatory_args.add_argument('-s', '--suffix', required=True, type=str,
                                help='Folder suffix, CoralNet or Biigle.')
    mandatory_args.add_argument('-p', '--platform', required=True, type=int,
                                help='Platform: for CoralNet enter 0, for Biigle enter 1.')
    mandatory_args.add_argument('-o', '--ofolder', required=True, type=str,
                                help='Output folder. Created if does not exist yet.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')
    optional_args.add_argument('-t', required=False, type=str, default='coralnet_to_biigle.csv',
                                help='CoralNet to BIIGLE label translation table.')
    optional_args.add_argument('-n', required=False, type=int, default=10,
                                help='Number of patches per label.')
    return parser


def create_portfolio(input_folder, suffix, platform, n_samples, fname_translation, ofolder):
    # Create ofolder if does not exist yet
    if not os.path.isdir(ofolder):
        print('\nCreating new output folder: {}'.format(ofolder))
        os.makedirs(ofolder)
    else:
        print('\nOutput folder already exists: {}'.format(ofolder))

    # Translation table between CoralNet and BIIGLE
    df_translation = pd.read_csv(fname_translation)
    platform = 'BIIGLE' if platform else 'CoralNet'
    labels_of_interest = df_translation[platform].unique().tolist()
    # Init dict of filenames
    dict_fname = {label: [] for label in labels_of_interest}
    # Create label folders
    print('\nCreating label sub-folders if do not exist...')
    for label in labels_of_interest:
        label_ofolder = os.path.join(ofolder, label)
        if not os.path.isdir(label_ofolder):
            os.makedirs(label_ofolder)

    # Loop across surveys
    print('\nLooking for samples...')
    for survey_name in os.listdir(input_folder):
        annotation_folder = os.path.join(input_folder, survey_name, survey_name + suffix)
        if os.path.isdir(annotation_folder):
            print('\tFor survey {} ...'.format(survey_name))
            for label in labels_of_interest:
                label_folder = os.path.join(annotation_folder, label)
                if os.path.isdir(label_folder):
                    for img in os.listdir(label_folder):
                        if img.endswith(".jpg"):
                            ifname = os.path.join(label_folder, img)
                            oimg = survey_name + "_" +img if platform == "BIIGLE" else img
                            ofname = os.path.join(ofolder, label, oimg)
                            dict_fname[label].append([ifname, ofname])

    # Feed portfolio
    print('\nFeeding portfolio...')
    for label in labels_of_interest:
        print('\tFor label {} ...'.format(label))
        candidates = dict_fname[label]
        if len(candidates) > n_samples:
            selected = random.sample(candidates, n_samples)
        else:
            selected = candidates
        for ifname, ofname in selected:
            shutil.copyfile(ifname, ofname)

    print('\n\n---------- Finished ----------\n\n')


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    create_portfolio(input_folder=args.input_folder,
                     suffix=args.suffix,
                     platform=args.platform,
                     n_samples=args.n,
                     fname_translation=args.t,
                     ofolder=args.ofolder)


if __name__ == "__main__":
    main()