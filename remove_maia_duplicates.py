import os
import math
import argparse
from tqdm import tqdm

from biigle.biigle import Api


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')
    mandatory_args.add_argument('-e', '--email', required=True, type=str,
                                help='Email address used for BIIGLE account.')
    mandatory_args.add_argument('-t', '--token', required=True, type=str,
                                help='BIIGLE API token. To generate one: https://biigle.de/settings/tokens')
    mandatory_args.add_argument('-d', '--date', required=True, type=str,
                                help='Date when MAIA candidates were integrated.')
    mandatory_args.add_argument('-i', '--label-tree-id', dest='label_tree_id', required=True, type=int,
                                help='Label tree ID.')
    mandatory_args.add_argument('-s', '--survey-name', dest='survey_name', required=True, type=str,
                                help='Survey name, eg NBP1402.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-l', '--label-id', dest='label_id', required=False, type=int,
                               help='Label ID to clean. If indicated, only annotations from this label are reviewed. '
                                    'Otherwise, all patches are reviewed. You can find the ID of a label in the JSON '
                                    'output of the label tree, eg https://biigle.de/api/v1/label-trees/1, by replacing '
                                    '"1" by the ID of your label-tree of interest.')
    optional_args.add_argument('-r', '--range-image', dest='range_image', required=False, type=str,
                               help='Range of image ID for which the cleaning is needed, separated by commas, eg'
                                    '"1234,5678".')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')

    return parser


def get_survey(surveys, survey_name):
    for survey in surveys:
        if survey["name"] == survey_name:
            return survey
    print("Survey not found: {}.".format(survey_name))
    return


def remove_maia_duplicates(email, token, label_tree_id, survey_name, maia_date, range_image=None, label_id=None):
    # Init API
    api = Api(email, token)

    # Get all surveys
    surveys = api.get('volumes').json()
    # Get info for survey of interest
    survey_dict = get_survey(surveys, survey_name)
    survey_id = survey_dict['id']

    # Get all labels from label tree
    if label_id is None:
        label_list = api.get('label-trees/{}'.format(label_tree_id)).json()['labels']
    else:
        label_list = [{'id': label_id}]

    cmpt_new = 0
    # Loop through labels
    for label in label_list:
        # Get annotations
        annotation_list = api.get('volumes/{}/annotations/filter/label/{}'.format(survey_id, label['id'])).json()

        if len(annotation_list):
            print('\nProcessing Label ID: {}.'.format(label['id']))
            annotation_id_list = list(annotation_list.keys())
            for id_ in annotation_id_list:
                annotation_info = api.get('annotations/{}'.format(id_)).json()
                if annotation_info['created_at'].startswith(maia_date):
                    if range_image is not None and annotation_info['image_id'] in \
                            list(range(range_image[0], range_image[1]+1)):
                        labels_in_img = [l['labels'][0]['label_id'] for l in
                                         api.get('images/{}/annotations'.format(annotation_info['image_id'])).json()]
                        if len(labels_in_img) > 1:
                            print(api.get('images/{}/annotations'.format(annotation_info['image_id'])).json())
                            print('\tDeleting: ')
                            print(annotation_info)
                            api.delete('annotations/{}'.format(id_))
                        else:
                            cmpt_new += 1
                    else:
                        cmpt_new += 1

    print('\nNb of new annotations thanks of MAIA: {}.'.format(cmpt_new))

    print('\n\n---------- Finished ----------\n\n')


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    remove_maia_duplicates(email=args.email,
                           token=args.token,
                           label_tree_id=args.label_tree_id,
                           survey_name=args.survey_name,
                           maia_date=args.date,
                           range_image=[int(r) for r in args.range_image.split(',')],
                           label_id=args.label_id)


if __name__ == "__main__":
    main()