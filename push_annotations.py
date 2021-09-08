import os
import shutil
import argparse
import requests
import pandas as pd
from tqdm import tqdm
from biigle.biigle import Api


# Example:
#   python push_annotations.py -e charley.gros@gmail.com -t SVRTBSUtVcQXZHjkNOxI29Zg2yu0nuhw -i 839 -d C:\Users\cgros\Documents\BIIGLE_library\TO_BE_UPLOADED -l 178966


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
    mandatory_args.add_argument('-d', '--datafolder', required=True, type=str,
                                help='Data folder.')
    mandatory_args.add_argument('-o', '--ofname', required=True, type=str,
                                help='CSV filename to save old annotations.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-l', '--label-id', dest='label_id', required=False, type=int,
                               help='Label ID to push. If indicated, only patches from this label are pushed. '
                                    'Otherwise, all patches are pushed. You can find the ID of a label in the JSON '
                                    'output of the label tree, eg https://biigle.de/api/v1/label-trees/1, by replacing '
                                    '"1" by the ID of your label-tree of interest.')
    optional_args.add_argument('-c', '--csv-done', dest='excel_done', required=False, type=str,
                               help='Excel used to track the changes between old and new tree. CSV file')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')

    return parser


def get_label_info(labels, label_id):
    for label in labels:
        if label["id"] == label_id:
            return label
    print("Label ID not found: {}.".format(label_id))
    return

def get_label_name(labels, label_id):
    label_info = get_label_info(labels, label_id)
    label_name = label_info["name"]
    if not label_info["parent_id"] is None:
        parent_info = get_label_info(labels, label_info["parent_id"])
        parent_name = parent_info["name"]
        label_name = parent_name + "_" + label_name
    return label_name


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


def push_patches(email, token, fname_excel_done, datafolder, label_tree_id, fname_o, label_id=None):
    # Init API
    api = Api(email, token)

    # Init excel_done
    if fname_excel_done is None:
        excel_done = {"done": [], "error": []}
        print("No tracking excel provided, starting from scratch.")
    else:
        df = pd.read_csv(fname_excel_done)
        excel_done = {"done": df["done"].values.tolist(),
                      "error": df["error"].values.tolist()}

    # Get label info
    label_tree_info = api.get('label-trees/{}'.format(label_tree_id)).json()
    #labels_info_list = add_parent_name(label_tree_info['labels'], labels_info_list)

    # Get new labels
    lst_label_new = label_tree_info["labels"]
    if not label_id is None:
        lst_label_new = [l for l in lst_label_new if l["id"] == label_id]
    #if label_id is None:
    #    lst_label_new = [l for l in os.listdir(datafolder) if os.path.isdir(os.path.join(datafolder, l))]
    #else:
    #    lst_label_new = [get_label_name(label_tree_info["labels"], label_id)]
    print(lst_label_new)

    # Loop across new labels
    for label_new in lst_label_new:
        name_label_new = get_label_name(label_tree_info["labels"], label_new["id"])
        print("\n" + name_label_new)
        folder_label = os.path.join(datafolder, name_label_new)
        if os.path.isdir(folder_label):
            lst_annotations = [a.split(".")[0] for a in os.listdir(folder_label)
                               if os.path.isfile(os.path.join(folder_label, a)) and a.endswith(".jpg")]
            lst_annotations = [a for a in lst_annotations if int(a) not in excel_done["done"] and int(a) not in excel_done["error"]]
            if len(lst_annotations):
                # Loop across annotations
                for id_annotation_old in tqdm(lst_annotations):
                    try:
                        info_annotation_old = api.get('image-annotations/{}'.format(int(id_annotation_old))).json()
                        info_annotation_new = {
                            "image_id": info_annotation_old["image_id"],
                            "shape_id": info_annotation_old["shape_id"],
                            "label_id": label_new["id"],
                            "confidence": 1.00,
                            "points": info_annotation_old["points"]
                        }
                        api.post("image-annotations", json=[info_annotation_new])
                        excel_done["done"].append(id_annotation_old)
                        excel_done["error"].append(None)
                    except:
                        excel_done["error"].append(id_annotation_old)
                        excel_done["done"].append(None)

                    df_done = pd.DataFrame.from_dict(excel_done)
                    df_done.to_csv(fname_o, index=False)

    print("\nSaving done annotations...")
    df_done = pd.DataFrame.from_dict(excel_done)
    df_done.to_csv(fname_o, index=False)

    exit()

    print('\n\n---------- Finished ----------\n\n')


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    push_patches(email=args.email,
                 token=args.token,
                 datafolder=args.datafolder,
                 fname_excel_done=args.excel_done,
                 label_tree_id=args.label_tree_id,
                 fname_o=args.ofname,
                 label_id=args.label_id)


if __name__ == "__main__":
    main()
