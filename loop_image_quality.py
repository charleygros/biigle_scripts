import os
import argparse
from tqdm import tqdm
#from compute_image_quality import compute_image_quality
from compute_image_quality_ter import compute_image_quality

# python loop_image_quality.py -i R:\IMAS\Antarctic_Seafloor\Clean_Data_For_Permanent_Storage -o iqs_results


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')
    mandatory_args.add_argument('-i', '--input', required=True, type=str,
                                help='Input folder containing all surveys.')
    mandatory_args.add_argument('-o', '--output', required=True, type=str,
                                help='Output folder where the results are saved, in a csv file. If this folder does '
                                     'not exist yet, it will be created.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-r', '--rm', dest='rm', required=False, type=bool, default=False,
                               help='If False, only surveys with no existing results will be processed. If True, all'
                                    ' surveys will be processed.')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')

    return parser


def get_survey_path(ifolder, prefix="_3_"):
    output_dict = {}
    for survey_name in os.listdir(ifolder):
        survey_folder = os.path.join(ifolder, survey_name)
        if os.path.isdir(survey_folder) and survey_name != "Empty_folder_structure":
            for subfolder in os.listdir(survey_folder):
                if prefix in subfolder:
                    output_dict[survey_name] = os.path.join(survey_folder, subfolder)

    return output_dict


def get_result_path(ofolder):
    output_dict = {}
    for f in os.listdir(ofolder):
        if f.endswith(".csv") and not f.endswith("_tmp.csv"):
            output_dict[f.split("_")[1]] = os.path.join(ofolder, f)

    return output_dict


def get_tmp_path(ofolder):
    output_dict = {}
    for f in os.listdir(ofolder):
        if f.endswith("_tmp.csv"):
            output_dict[f.split("_")[1]] = os.path.join(ofolder, f)

    return output_dict


def loop_image_quality(input_folder, output_folder, rm_existing=False):
    # Get path of folder containing images for each survey
    survey_path_dict = get_survey_path(ifolder=input_folder, prefix="_3_")
    # Get existing results
    result_path_dict = get_result_path(ofolder=output_folder)
    # Get unfinished results
    tmp_path_dict = get_tmp_path(ofolder=output_folder)

    # Redo or resume
    if rm_existing:
        for survey_name in result_path_dict:
            print("Removing old results from {} ...".format(survey_name))
            os.remove(result_path_dict[survey_name])
    else:
        for survey_name in result_path_dict:
            print("Results already available for {} - Skipping ...".format(survey_name))
            del survey_path_dict[survey_name]

    for survey_name in tqdm(survey_path_dict, desc="Looping across surveys"):
        print("\n\nSurvey: {} ...".format(survey_name))
        tmp_path = tmp_path_dict[survey_name] if survey_name in tmp_path_dict else None
        # Run process
        ofname = compute_image_quality(input_path=survey_path_dict[survey_name],
                                       output_path=output_folder,
                                       tmp_path=tmp_path,
                                       survey_name=survey_name)
        # Rename output file
        ofname_survey = os.path.join(output_folder, "results_"+survey_name+"_"+ofname.split("results_")[-1])
        os.rename(ofname, ofname_survey)
        # Remove tmp file
        if os.path.isfile(tmp_path):
            os.remove(tmp_path)


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    loop_image_quality(input_folder=args.input,
                       output_folder=args.output,
                       rm_existing=args.rm)


if __name__ == "__main__":
    main()
