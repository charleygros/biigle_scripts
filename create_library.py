import os
import shutil
import argparse
from tqdm import tqdm


# python create_library.py -i R:\IMAS\Antarctic_Seafloor\Clean_Data_For_Permanent_Storage\ -l funky_anemones -o ..\..\Docu
# ments\BIIGLE_library


ACCEPTED_IMAGE_FORMAT = ["jpg", "png", "JPG"]


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')
    mandatory_args.add_argument('-i', '--ifolder', required=True, type=str,
                                help='Input folder containing all surveys.')
    mandatory_args.add_argument('-l', '--label', required=True, type=str,
                                help='BIIGLE label name.')
    mandatory_args.add_argument('-o', '--ofolder', required=True, type=str,
                                help='Output folder where the BIIGLE label will be created and samples saved. It will '
                                     'be created if does not exist yet.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')

    return parser


def get_survey_path(ifolder, label_name, prefix="_6_VME_"):
    output_dict = {}
    for survey_name in os.listdir(ifolder):
        survey_folder = os.path.join(ifolder, survey_name)
        if os.path.isdir(survey_folder) and survey_name != "Empty_folder_structure":
            for subfolder in os.listdir(survey_folder):
                if prefix in subfolder:
                    label_folder = os.path.join(survey_folder, subfolder, label_name)
                    if os.path.isdir(label_folder):
                        output_dict[survey_name] = label_folder

    return output_dict


def get_image_path(survey_dict):
    output_lst = []
    for survey in survey_dict.keys():
        for fname in os.listdir(survey_dict[survey]):
            ext = fname.split(".")[-1]
            if ext in ACCEPTED_IMAGE_FORMAT:
                output_lst.append(os.path.join(survey_dict[survey], fname))
            else:
                if ext not in ["db"]:
                    print("\nUnknown extension: {} in {}.".format(ext, fname))
                    exit()
    return output_lst


def create_library(input_folder, label_name, output_folder):
    # Output folder
    if os.path.isdir(output_folder):
        print('\nOutput folder already exists: {}.'.format(output_folder))
    else:
        print('\nCreating output folder: {}.'.format(output_folder))
        os.makedirs(output_folder)
    # Output label folder
    output_folder = os.path.join(output_folder, label_name)
    # Output folder
    if os.path.isdir(output_folder):
        print('\nLabel output folder already exists: {}.'.format(output_folder))
    else:
        print('\nCreating label output folder: {}.'.format(output_folder))
        os.makedirs(output_folder)

    # Get surveys where the label is present
    survey_dict = get_survey_path(input_folder, label_name, prefix="_6_VME")

    # Get paths of images of interest
    fname_lst = get_image_path(survey_dict)
    print("\nFound {} annotations.".format(len(fname_lst)))

    # Copying annotations
    print("\nCopy annotations")
    for ifname in tqdm(fname_lst, desc="Pulling"):
        _, tail = os.path.split(ifname)
        ofname = os.path.join(output_folder, tail)
        shutil.copyfile(ifname, ofname)

    print('\n\n---------- Finished ----------\n\n')


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    create_library(input_folder=args.ifolder,
                   label_name=args.label,
                   output_folder=args.ofolder)


if __name__ == "__main__":
    main()
