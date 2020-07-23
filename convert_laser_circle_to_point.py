import copy
import argparse
from requests.exceptions import HTTPError
from biigle.biigle import Api


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')

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


# Enter your user email address here.
email = 'charley.gros@gmail.com'
# Enter your API token here.
token = 'DDV6vMU2TvQ0VQQI6bNQjfZ5X88ENc9B'
# ID of the laser point label.
label_name = "Laser Point"
label_id = 1558
# Project name
project_name = "CircumAntarctic Seafloor Biodiversity"
# Survey name
survey_name = "NBP1402"

api = Api(email, token)

projects = api.get('projects').json()
project_id = get_project_id(projects, project_name)

# Get the available annotation shapes.
# https://biigle.de/doc/api/index.html#api-Shapes-IndexShapes
shapes = api.get('shapes').json()
shapes = {s['name']: s['id'] for s in shapes}

# Get all surveys
surveys = api.get('volumes').json()
survey_dict = get_survey(surveys, survey_name)
if not survey_dict:
    exit()

post_data = {
    'shape_id': shapes['Point'],
    'label_id': label_id,
    'confidence': 1,
    'points': [],
}

can_batch_create = True
try:
    api.post('annotations')
except HTTPError as e:
    can_batch_create = False
print("\n... Batch processing: {}.".format(can_batch_create))

survey_id = survey_dict['id']
# Get the list of image IDs that belong to the survey.
image_ids = api.get('volumes/{}/images'.format(survey_id)).json()
print("\n\t... Found {} images.".format(len(image_ids)))

batch_size = 1
batch = []

print("\n... Looping across images.")
for image_id in image_ids:

    # Check if automatic laser point detection
    try:
        laser_info = api.get('images/{}/laserpoints'.format(image_id)).json()

        if laser_info:
            print('\tAlready a laser point for image {}, skipping.'.format(image_id))
            continue

    except:
        annotation_info = api.get('images/{}/annotations'.format(image_id)).json()
        laser_annotations = get_label_annotations(annotation_info, label_name)

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

                    print('\t\tWrong laser annotation shape on image {}.'.format(laser['image_id']))

                    # Get Laser circle center coordinates
                    post_data['points'] = laser['points'][:-1]

                    print('\t\t... Converting annotation {} to Point.'.format(laser["id"]))
                    if can_batch_create:
                        post_data['image_id'] = image_id
                        batch.append(copy.copy(post_data))
                        if len(batch) == batch_size:
                            api.post('annotations', json=batch)
                            batch = []
                    else:
                        # Create a new annotation for the image.
                        api.post('images/{}/annotations'.format(image_id), json=post_data)

                    # Delete wrong annotation
                    #api.delete('images/{}/annotations/filter/label/{}'.format(image_id, laser["id"]))
                    #exit()

                else:
                    print('\t\tCorrect laser annotation shape on image {}, annotation '
                          '{}.'.format(laser['image_id'], laser["id"]))
            exit()
        else:
            print('\tNo {} found for image {}, skipping.'.format(label_name, image_id))
            continue

if can_batch_create and len(batch) > 0:
   api.post('annotations', json=batch)

print('\n\n---------- Finished ----------\n\n')
