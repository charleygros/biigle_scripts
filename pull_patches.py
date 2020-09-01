import os
import shutil
import argparse
import requests
from tqdm import tqdm
from biigle.biigle import Api

# TODO:
#   - Add possibility to input multiple labels IDs

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
    mandatory_args.add_argument('-i', '--label-tree-id', dest='label_tree_id', required=True, type=int,
                                help='Label tree ID.')
    mandatory_args.add_argument('-o', '--ofolder', required=True, type=str,
                                help='Output folder. It will be created if does not exist yet.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-l', '--label-id', dest='label_id', required=False, type=int,
                               help='Label ID to download. If indicated, only patches from this label are pulled. '
                                    'Otherwise, all patches are downloaded. You can find the ID of a label in the JSON '
                                    'output of the label tree, eg https://biigle.de/api/v1/label-trees/1, by replacing '
                                    '"1" by the ID of your label-tree of interest.')
    optional_args.add_argument('-r', '--range-image', dest='range_image', required=False, type=str,
                               help='Range of image ID of interest, separated by commas, eg'
                                    '"1234,5678".')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')

    return parser


def get_label_info(labels, label_id):
    for label in labels:
        if label["id"] == label_id:
            return label
    print("Label ID not found: {}.".format(label_id))
    return


def get_survey(surveys, survey_name):
    for survey in surveys:
        if survey["name"] == survey_name:
            return survey
    print("Survey not found: {}.".format(survey_name))
    return


def add_parent_name(label_tree_info, labels_info_list):
    id_of_interest = [l['id'] for l in label_tree_info]

    out_list = []
    for label_info in labels_info_list:
        # Discard
        if not label_info['id'] in id_of_interest:
            continue

        parent_info = [label_tree_info_ for label_tree_info_ in label_tree_info
                       if label_tree_info_['id'] == label_info['parent_id']]
        if len(parent_info) == 0:  # No parent
            parent_name = ''
        elif len(parent_info) == 1:
            parent_name = parent_info[0]['name']
        else:
            print('ERROR: multiple parents: {}.'.format(label_info))
            exit()

        label_info['parent_name'] = parent_name
        out_list.append(label_info)

    return out_list


def pull_patches(email, token, survey_name, label_tree_id, output_folder, range_image=[], label_id=None):
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
        print('\nCreating output folder: {}.'.format(output_folder))
        os.makedirs(output_folder)

    # Get label info
    labels_info_list = api.get('volumes/{}/annotation-labels'.format(survey_id)).json()
    label_tree_info = api.get('label-trees/{}'.format(label_tree_id)).json()
    labels_info_list = add_parent_name(label_tree_info['labels'], labels_info_list)

    # Pick the label of interest
    if label_id != None:
        labels_info_list = [label_info for label_info in labels_info_list if label_info['id'] == label_id]

    # Init patch URL
    patch_url = 'https://biigle.de/storage/largo-patches/{}/{}/{}/{}.jpg'

    # List annotations of interest
    if len(range_image):
        list_img_annotations = []
        images = api.get('volumes/{}/files'.format(survey_id)).json()
        images_range = list(range(range_image[0], range_image[1]+1))
        images_of_interest = [ii for ii in images_range if ii in images]
        for image_id in tqdm(images_of_interest, desc="Fetching annotations of interest"):
            try:
                annotations_list = api.get('images/{}/annotations'.format(image_id)).json()
                annotations_id_list = [a['id'] for a in annotations_list]
                list_img_annotations = list_img_annotations + annotations_id_list
            except:
                pass
    else:
        list_img_annotations = None

    for label_dict in labels_info_list:
        annotations = api.get('volumes/{}/image-annotations/filter/label/{}'.format(survey_id, label_dict['id'])).json()
        if len(annotations) > 0:
            # Label full name
            full_name = label_dict['name'].replace(' ', '_')
            if len(label_dict['parent_name']) > 0:
                full_name = label_dict['parent_name'].replace(' ', '_') + '-' + full_name
            print('\tPulling patches for Label: {}.'.format(full_name))
            print('\tFound {} annotations.'.format(len(annotations)))

            # Label output folder
            label_ofolder = os.path.join(output_folder, full_name)
            if os.path.isdir(label_ofolder):
                print('\tOutput folder already exists: {}.'.format(label_ofolder))
            else:
                print('\tCreating output folder: {}.'.format(label_ofolder))
                os.makedirs(label_ofolder)

            for annotation_id, image_uuid in tqdm(annotations.items(), desc="Pulling"):
                if list_img_annotations is None or (len(list_img_annotations) > 0 and
                                                    annotation_id in list_img_annotations):
                    url = patch_url.format(image_uuid[:2], image_uuid[2:4], image_uuid, annotation_id)
                    patch = requests.get(url, stream=True)
                    if patch.ok != True:
                        raise Exception('Failed to fetch {}'.format(url))
                    with open(os.path.join(label_ofolder, '{}.jpg'.format(annotation_id)), 'wb') as f:
                        patch.raw.decode_content = True
                        shutil.copyfileobj(patch.raw, f)

    print('\n\n---------- Finished ----------\n\n')


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    pull_patches(email=args.email,
                 token=args.token,
                 survey_name=args.survey_name,
                 label_tree_id=args.label_tree_id,
                 output_folder=args.ofolder,
                 range_image=[int(r) for r in args.range_image.split(',')] if args.range_image is not None else [],
                 label_id=args.label_id)


if __name__ == "__main__":
    main()