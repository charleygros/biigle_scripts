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
    mandatory_args.add_argument('-i', '--label-tree-id', dest='label_tree_id', required=True, type=int,
                                help='Label tree ID.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
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
    out_list = []
    for label_info in labels_info_list:
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


def clean_tree(email, token, label_tree_id):
    # Init API
    api = Api(email, token)

    # Get label tree info
    label_tree_info = api.get('label-trees/{}'.format(label_tree_id)).json()['labels']
    z_ids = []
    for label_info in label_tree_info:
        if label_info['name'].startswith('z_'):
            z_ids.append(label_info['id'])

    # Remove z kids
    for label_info in label_tree_info:
        if label_info['parent_id'] in z_ids:
            try:
                api.post('label-trees/{}/merge-labels'.format(label_tree_id), json={'remove': [label_info['id']]})
            except:
                print(label_info)
                #print(api.get('labels/{}/annotations'.format(label_info['id'])).json())
                #print(api.get('annotations/{}'.format('7875997')).json())

    # Empty parents
    for zid in z_ids:
        parent = api.get('labels/{}/annotations'.format(zid)).json()
        for annotation_id in parent:
            api.delete('annotations/{}'.format(annotation_id))

    # Remove parents
    #api.post('label-trees/{}/merge-labels'.format(label_tree_id), json={'remove': z_ids})

    print('{}'.format('\n'.join([(' '.join([l['name'], str(l['id']), str(l['parent_id'])])) for l in label_tree_info])))

    # Create new parent
    #api.post('label-trees/{}/labels'.format(label_tree_id), json={'color': "#0be6c8",
    #                                                               "name": "HydroCorals"
    #                                                               })

    # Move HydroCorals
    #api.put('labels/{}'.format(133260), json={"parent_id": 155169, "name": 'Branching'})
    #api.put('labels/{}'.format(133261), json={"parent_id": 155169, "name": 'Encrusting'})

    # Rename Hydroids
    #api.put('labels/{}'.format(133262), json={"name": 'Colonial feather'})
    #api.put('labels/{}'.format(133263), json={"name": 'Solitary'})
    #api.put('labels/{}'.format(133259), json={"name": 'Matrix'})
    #api.put('labels/{}'.format(133258), json={"name": 'Hydroids'})

    print('\n\n---------- Finished ----------\n\n')


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    clean_tree(email=args.email,
               token=args.token,
               label_tree_id=args.label_tree_id)


if __name__ == "__main__":
    main()