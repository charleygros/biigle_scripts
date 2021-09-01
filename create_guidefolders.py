import os
import argparse

# python create_guidefolders.py -i C:\Users\cgros\Documents\BIIGLE_library -o C:\Users\cgros\Documents\BIIGLE_libra
# ry\__SHARED\Guide


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')
    mandatory_args.add_argument('-i', '--ifolder', required=True, type=str,
                                help='Input folder containing raw data.')
    mandatory_args.add_argument('-o', '--ofolder', required=True, type=str,
                                help='Output folder for the guide.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')

    return parser


def create_guidefolders(input_folder, output_folder, filter_start="_"):
    for i_fname in os.listdir(input_folder):
        i_path = os.path.join(input_folder, i_fname)
        if not i_fname.startswith(filter_start) and not i_fname.startswith('.') and os.path.isdir(i_path):
            o_path = os.path.join(output_folder, i_fname)
            print('Creating {} ...'.format(o_path))
            os.makedirs(o_path)


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    create_guidefolders(input_folder=args.ifolder,
                        output_folder=args.ofolder,
                        filter_start="_")


if __name__ == "__main__":
    main()