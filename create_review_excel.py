import os
import argparse
import pandas as pd

# python create_review_excel.py -i C:\Users\cgros\Documents\BIIGLE_library\__SHARED\Guide -o _comments.xlsx

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


def create_review_excel(input_folder, output_fname):
    if not output_fname.endswith(".xlsx"):
        print("Please enter xlsx filename as ofname.")
        exit()

    for i_category in os.listdir(input_folder):
        i_path = os.path.join(input_folder, i_category)
        output_path = os.path.join(i_path, output_fname)
        if os.path.isdir(i_path): # and not os.path.isfile(output_path):
            output_dct = {"image_ID": [], "comment": []}
            print("\nCategory: {} ...".format(i_category))
            for i_image in os.listdir(i_path):
                if is_image(i_image):
                    filename, ext = os.path.splitext(i_image)
                    output_dct["image_ID"].append(filename)
                    output_dct["comment"].append("")

            output_pd = pd.DataFrame.from_dict(output_dct)
            #output_pd.image_ID = output_pd.image_ID.astype(int)
            output_pd.sort_values("image_ID", ascending=True, inplace=True)
            print("Found {} samples.".format(len(output_pd)))

            if len(output_pd):
                print("Saving in {} ...".format(output_path))
                print(output_pd.head())
                output_pd.to_excel(output_path, index=False, index_label=False, columns=["image_ID", "comment"])


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    create_review_excel(input_folder=args.ifolder,
                        output_fname=args.ofname)


if __name__ == "__main__":
    main()