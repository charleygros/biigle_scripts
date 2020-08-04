import os
import pandas as pd
import argparse
from biigle.biigle import Api

LABEL_NAME = "Laser Point"


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')
    mandatory_args.add_argument('-e', '--email', required=True, type=str,
                                help='Email address used for BIIGLE account.')
    mandatory_args.add_argument('-t', '--token', required=True, type=str,
                                help='BIIGLE API token. To generate one: https://biigle.de/settings/tokens')
    mandatory_args.add_argument('-s', '--survey-name', dest='survey_name', required=True, type=str,
                                help='Survey name, eg NBP1402.')
    mandatory_args.add_argument('-o', '--ofolder', required=True, type=str,
                                help='Output folder. It will be created if does not exist yet.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')

    return parser


def get_survey(surveys, survey_name):
    for survey in surveys:
        if survey["name"] == survey_name:
            return survey
    print("Survey not found: {}.".format(survey_name))
    return


def get_label_annotations(annotation_info, label_name):
    new_annotation_list = []
    for annotation in annotation_info:
        for labels in annotation['labels']:
            if labels['label']['name'] == label_name:
                new_annotation_list.append(annotation)
    return new_annotation_list


def fetch_incorrect_laser(email, token, survey_name, ofolder):
    # Init API
    api = Api(email, token)

    # Get all surveys
    surveys = api.get('volumes').json()
    # Get info for survey of interest
    survey_dict = get_survey(surveys, survey_name)
    survey_id = survey_dict['id']

    # Get the list of image IDs that belong to the survey of interest
    image_ids = api.get('volumes/{}/images'.format(survey_id)).json()
    print("\n\t... Found {} images.".format(len(image_ids)))

    # Init result dict
    dict = {'image_fname': [], 'image_id': [], 'n_laser': []}

    print("\n... Looping across images.")
    for image_id in image_ids:
        # Get all annotations for the current image
        annotation_info = api.get('images/{}/annotations'.format(image_id)).json()
        # Get laser annotations for the given image
        laser_annotations = get_label_annotations(annotation_info, LABEL_NAME)

        # Check if nb laser annotations is wrong
        if len(laser_annotations) != 2:
            dict['image_id'].append(image_id)
            dict['image_fname'].append(api.get('images/{}'.format(image_id)).json()['filename'])
            dict['n_laser'].append(len(laser_annotations))

    # Output folder
    if os.path.isdir(ofolder):
        print('\nOutput folder already exists: {}.'.format(ofolder))
    else:
        print('\nCreating output folder: {}.'.format(ofolder))
        os.makedirs(ofolder)
    fname_out = os.path.join(ofolder, survey_name+'_incorrect_laser.csv')
    df = pd.DataFrame.from_dict(dict)
    df.to_csv(fname_out)
    print('\nSaving results in: {}.'.format(fname_out))

    print('\n\n---------- Finished ----------\n\n')


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    fetch_incorrect_laser(email=args.email,
                          token=args.token,
                          survey_name=args.survey_name,
                          ofolder=args.ofolder)


if __name__ == "__main__":
    main()
