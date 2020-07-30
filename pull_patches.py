import argparse
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
    optional_args.add_argument('-l', '--label-name', dest='label_name', required=False, type=str,
                               help='Label name to download. If indicated, only patches from this label are pulled. '
                                    'Otherwise, all patches are downloaded.')
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


def pull_patches(email, token, survey_name, label_name=None):
    # Init API
    api = Api(email, token)

    # Get the available annotation shapes.
    # https://biigle.de/doc/api/index.html#api-Shapes-IndexShapes
    shapes = api.get('shapes').json()
    shapes = {s['name']: s['id'] for s in shapes}

    # Get all surveys
    surveys = api.get('volumes').json()
    # Get info for survey of interest
    survey_dict = get_survey(surveys, survey_name)
    survey_id = survey_dict['id']


def main():
    parser = get_parser()
    args = parser.parse_args()
    print(args)
    # Run function
    #pull_patches(email=args.email,
    #             token=args.token,
    #             survey_name=args.survey_name)


if __name__ == "__main__":
    main()