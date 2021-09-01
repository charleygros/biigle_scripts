import json
import argparse
import pandas as pd
from biigle.biigle import Api

# Example:
#   python modify_label_tree.py -e charley.gros@gmail.com -t SVRTBSUtVcQXZHjkNOxI29Zg2yu0nuhw -i new_label_tree.csv -n 839


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')
    mandatory_args.add_argument('-e', '--email', required=True, type=str,
                                help='Email address used for BIIGLE account.')
    mandatory_args.add_argument('-t', '--token', required=True, type=str,
                                help='BIIGLE API token. To generate one: https://biigle.de/settings/tokens')
    mandatory_args.add_argument('-i', '--csv-label-infos', dest='csv_label_infos', required=True, type=str,
                                help='CSV file containing the label tree infos.')
    mandatory_args.add_argument('-n', '--label-tree-id', dest='label_tree_id', required=True, type=int,
                                help='Label tree ID.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')

    return parser


def create_label(api, label_tree_id, name, parent_id, color):
    dict = {"create": [{'name': name, 'color': color}]}
    if not parent_id is None:
        dict["create"][0]['parent_id'] = parent_id
    print(dict)
    api.post('label-trees/{}/merge-labels'.format(label_tree_id), json=dict)


def modify_label_tree(email, token, df_tree_changes, label_tree_id):
    # Init API
    api = Api(email, token)

    # Loop through rows
    lst_labels = []
    for i_row, row in df_tree_changes.iterrows():
        parent, label, color = row["parent"], row["label"], row["color"]
        print(parent, label, color)

        parent_id = None
        if (not parent in lst_labels) and (parent == parent):
            create_label(api, label_tree_id, name=parent, parent_id=None, color=color)

        if (parent != parent):
            create_label(api, label_tree_id, name=label, parent_id=None, color=color)
        else:
            info_tree = api.get('label-trees/{}'.format(label_tree_id)).json()['labels']
            for label_info in info_tree:
                if label_info['name'] == parent:
                    parent_id = label_info['id']
            lst_labels.append(parent)
            create_label(api, label_tree_id, name=label, parent_id=parent_id, color=color)

        lst_labels.append(label)

    print('\n\n---------- Finished ----------\n\n')


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Read changes
    df_tree_changes = pd.read_csv(args.csv_label_infos)
    print(df_tree_changes.head())

    # Run function
    modify_label_tree(email=args.email,
                      token=args.token,
                      df_tree_changes=df_tree_changes,
                      label_tree_id=args.label_tree_id)


if __name__ == "__main__":
    main()
