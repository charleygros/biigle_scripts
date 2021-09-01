import os
import argparse
import pandas as pd

# python create_noideaexcel.py -i C:\Users\cgros\Documents\BIIGLE_library\__SHARED\Questions_Candice\Q3 -o _comments.xlsx

ACCEPTED_IMAGE_FORMAT = [".jpg", ".png", ".JPG"]


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')
    mandatory_args.add_argument('-i', '--ifolder', required=True, type=str,
                                help='Input folder containing data.')
    mandatory_args.add_argument('-o', '--ofname', required=True, type=str,
                                help='Filename for the xslx. Will be saved in each category folder.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')

    return parser


def is_image(fname):
    for f_format in ACCEPTED_IMAGE_FORMAT:
        if fname.endswith(f_format):
            return True
    return False


def create_noidea_excel(input_folder, output_fname):
    if not output_fname.endswith(".xlsx"):
        print("Please enter xlsx filename as ofname.")
        exit()

    output_dct = {"image_ID": [], "comment": []}
    for i_image in os.listdir(input_folder):
        if is_image(i_image):
            output_dct["image_ID"].append(i_image.split(".")[0])
            output_dct["comment"].append("")

    output_pd = pd.DataFrame.from_dict(output_dct)
    print("Found {} samples.".format(len(output_pd)))

    if len(output_pd):
        output_path = os.path.join(input_folder, output_fname)
        print("Saving in {} ...".format(output_path))
        output_pd.to_excel(output_path, index=False, index_label=False, columns=["image_ID", "comment"])


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    create_noidea_excel(input_folder=args.ifolder,
                        output_fname=args.ofname)


if __name__ == "__main__":
    main()