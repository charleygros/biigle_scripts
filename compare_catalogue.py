import os
import shutil
import argparse
from tqdm import tqdm


# python compare_catalogue.py -s C:\Users\cgros\Documents\BIIGLE_library\__SHARED\Guide_REF -d C:\Users\cgros\Documents\BIIGLE_library\__SHARED\Guide_VME_morphotaxa_Candice


ACCEPTED_IMAGE_FORMAT = ["jpg", "png", "JPG", "PNG"]


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')
    mandatory_args.add_argument('-s', '--sourcefolder', required=True, type=str,
                                help='Source catalogue.')
    mandatory_args.add_argument('-d', '--destfolder', required=True, type=str,
                                help='Destination catalogue.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')

    return parser


def get_dct(folder):
    dct = {}
    for taxa in os.listdir(folder):
        taxa_folder = os.path.join(folder, taxa)
        if os.path.isdir(taxa_folder):
            for img in os.listdir(taxa_folder):
                img_path = os.path.join(taxa_folder, img)
                if any([img.endswith(ext) for ext in ACCEPTED_IMAGE_FORMAT]) and os.path.isfile(img_path):
                    if not taxa in dct:
                        dct[taxa] = []
                    dct[taxa].append(img.split(".")[0])
    return dct


def compare_catalogue(source_folder, destination_folder):
    # Get catalogues
    src_dct = get_dct(source_folder)
    dest_dct = get_dct(destination_folder)

    # Compare catalogues
    for taxa in src_dct:
        print("\n"+taxa)
        for img in src_dct[taxa]:
            if img not in dest_dct[taxa]:
                new_label = [taxa_ for taxa_ in dest_dct if img in dest_dct[taxa_]]
                print("\t {} towards {}".format(img, new_label))

    print('\n\n---------- Finished ----------\n\n')


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    compare_catalogue(source_folder=args.sourcefolder,
                      destination_folder=args.destfolder)


if __name__ == "__main__":
    main()
