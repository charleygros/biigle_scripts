import os
import shutil
import argparse
import requests
from biigle.biigle import Api


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
    optional_args.add_argument('-l', '--label-id', dest='label_id', required=False, type=str,
                               help='Label ID to download. If indicated, only patches from this label are pulled. '
                                    'Otherwise, all patches are downloaded. You can find the ID of a label in the JSON '
                                    'output of the label tree, eg https://biigle.de/api/v1/label-trees/1, by replacing '
                                    '"1" by the ID of your label-tree of interest.')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')

    return parser


def get_project_id(projects, project_name):
    for project in projects:
        if project["name"] == project_name:
            return project["id"]
    print("Project not found: {}.".format(project_name))
    return


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


def pull_patches(email, token, survey_name, output_folder, label_id=None):
    # Init API
    api = Api(email, token)

    # Get all surveys
    surveys = api.get('volumes').json()
    # Get info for survey of interest
    survey_dict = get_survey(surveys, survey_name)
    survey_id = survey_dict['id']

    # Output folder
    if os.path.isdir(output_folder):
        print('\nOutput folder already exists: {}.'.format(output_folder))
    else:
        print('\nCreating output folder: {}.')
        os.makedirs(output_folder)

    # Get annotations
    # TODO: When label_id is None
    endpoint_url = '{}s/{}/annotations/filter/label/{}'
    annotations = api.get(endpoint_url.format("volume", survey_id, label_id)).json()
    print('\nFound {} annotations.'.format(len(annotations)))

    # Init patch URL
    patch_url = 'https://biigle.de/storage/largo-patches/{}/{}/{}/{}.jpg'

    """
    for annotation_id, image_uuid in annotations.items():
        url = patch_url.format(image_uuid[:2], image_uuid[2:4], image_uuid, annotation_id)
        print('Fetching', url)
        patch = requests.get(url, stream=True)
        if patch.ok != True:
            raise Exception('Failed to fetch {}'.format(url))
        with open('{}.jpg'.format(annotation_id), 'wb') as f:
            patch.raw.decode_content = True
            shutil.copyfileobj(patch.raw, f)
    """
    print('\n\n---------- Finished ----------\n\n')


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    pull_patches(email=args.email,
                 token=args.token,
                 survey_name=args.survey_name,
                 output_folder=args.ofolder,
                 label_id=args.label_id)


if __name__ == "__main__":
    main()