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

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
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


def convert_laser_circle_to_point(email, token, survey_name):
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

    # Get the list of image IDs that belong to the survey of interest
    image_ids = api.get('volumes/{}/images'.format(survey_id)).json()
    print("\n\t... Found {} images.".format(len(image_ids)))

    print("\n... Looping across images.")
    for image_id in image_ids:
        # Check if laser point already exist
        try:
            laser_info = api.get('images/{}/laserpoints'.format(image_id)).json()

            if laser_info:
                print('\tAlready a laser point for image {}, skipping.'.format(image_id))
                continue

        except:
            # Get all annotations for the current image
            annotation_info = api.get('images/{}/annotations'.format(image_id)).json()
            # Get laser annotations for the given image
            laser_annotations = get_label_annotations(annotation_info, LABEL_NAME)

            # Check if there is some laser annotations
            if len(laser_annotations):
                # Loop across laser points
                for laser in laser_annotations:
                    # Check if laser shape is not a Point
                    if laser['shape_id'] != shapes['Point']:
                        # Check if laser shape is a circle
                        if laser['shape_id'] != 4:
                            print("NOT IMPLEMENTED YET: laser shape: {}.".format(laser['shape_id']))
                            exit()

                        print('\t\tImage {} --> converting annotation {} to Point.'.format(laser['image_id'],
                                                                                           laser["id"]))
                        api.put('annotations/{}'.format(laser["id"]),
                                json={
                                    'shape_id': shapes['Point'],
                                    'points': laser['points'][:-1]
                                })

                    else:
                        print('\t\tCorrect laser annotation shape on image {}, annotation '
                              '{}.'.format(laser['image_id'], laser["id"]))

            else:
                print('\tNo {} found for image {}, skipping.'.format(LABEL_NAME, image_id))
                continue

    print('\n\n---------- Finished ----------\n\n')


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    convert_laser_circle_to_point(email=args.email,
                                  token=args.token,
                                  survey_name=args.survey_name)


if __name__ == "__main__":
    main()
