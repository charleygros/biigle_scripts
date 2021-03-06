import os
import copy
import shutil
import argparse
from datetime import datetime
from tqdm import tqdm
import pandas as pd

from biigle.biigle import Api
import utils as biigle_utils


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')
    mandatory_args.add_argument('-e', '--email', required=True, type=str,
                                help='Email address used for BIIGLE account.')
    mandatory_args.add_argument('-t', '--token', required=True, type=str,
                                help='BIIGLE API token. To generate one: https://biigle.de/settings/tokens')
    mandatory_args.add_argument('-i', '--ifolder', required=True, type=str,
                                help='Input folder, filled with patches to move.')
    mandatory_args.add_argument('-o', '--ofolder', required=True, type=str,
                                help='Output folder, where Source and Destination folders are located.')
    mandatory_args.add_argument('-s', '--source', dest='source', required=True, type=str,
                                help='Source label.')
    mandatory_args.add_argument('-d', '--destination', dest='destination', required=True, type=str,
                                help='Destination label.')
    mandatory_args.add_argument('-l', '--label-tree-id', dest='label_tree_id', required=True, type=int,
                                help='Label tree ID.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-b', '--batch-size', dest='batch_size', required=False, type=int, default=100,
                                help='Batch size.')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')

    return parser


def move_annotations(email, token, input_folder, output_folder, label_tree_id, src, dest, batch_size=100):
    # Init API
    api = Api(email, token)

    # Get all labels from label tree
    label_tree_info = api.get('label-trees/{}'.format(label_tree_id)).json()['labels']
    label_dict = biigle_utils.get_folders_match_tree(label_tree_info)

    # Check folders exist
    src_folder = os.path.join(output_folder, src)
    dest_folder = os.path.join(output_folder, dest)
    for f in [input_folder, src_folder]:
        if not os.path.isdir(f):
            print('\nFolder not found: {}'.format(f))
            exit()
    if not os.path.isdir(dest_folder) and dest != "NOT_VME":
        if dest in label_dict:
            print('\nCreating destination folder: {}'.format(dest_folder))
            os.makedirs(dest_folder)
        else:
            print('\nUnknown destination category: {}'.format(dest))
            exit()


    # Log file
    fname_log = os.path.join(output_folder, "logfile_"+datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+".csv")
    dict_log = {"annotation_id": [], "from": [], "to": [], "who": []}

    # Get annotation fnames
    input_fname_list = [f for f in os.listdir(input_folder) if f.endswith('.jpg')]

    # Check if all annotations from input folder are coming from source folder
    input_fname_list_new = []
    for idx, f in enumerate(input_fname_list):
        src_fname_cur = os.path.join(src_folder, f)
        if not os.path.isfile(src_fname_cur):
            print('\tWARNING: {} is not found in {}'.format(f, src_folder))
        else:
            input_fname_list_new.append(f)
    print('\nFound {} annotations to move.'.format(len(input_fname_list_new)))

    # Nested list
    input_fname_nested = [input_fname_list_new[i:i + batch_size]
                          for i in range(0, len(input_fname_list_new), batch_size)]

    # Move per batch
    for fname_sublist in tqdm(input_fname_nested, desc="Reviewing"):
        annotation_ids = [f.split('.jpg')[0] for f in fname_sublist]
        annotation_infos = [api.get('image-annotations/{}'.format(annotation_id)).json()
                            for annotation_id in annotation_ids]

        # Create batch
        batch = []
        for annotation_info in annotation_infos:
            if dest != "NOT_VME":
                annotation_info["label_id"] = label_dict[dest]['id']
            annotation_info["confidence"] = 1.00
            batch.append(copy.copy(annotation_info))

        # Run batch
        if dest != "NOT_VME":
            api.post('image-annotations', json=batch)

        # Cleanup
        for batch_info in batch:
            # Print info
            image_info = api.get('images/{}'.format(batch_info['image_id'])).json()
            print('\n\tChange annotation {} from {} to {} on image {} (image ID: {}).'.format(batch_info['id'],
                                                                                              src,
                                                                                              dest,
                                                                                              image_info['filename'],
                                                                                              image_info['id']))

            # Detach old label
            old_label_id = [ann['id'] for ann in api.get('image-annotations/{}/labels'.format(batch_info['id'])).json()
                            if ann["label_id"] == label_dict[src]['id']][0]
            api.delete('image-annotation-labels/{}'.format(old_label_id))

            # Move file
            if dest != "NOT_VME":
                shutil.move(os.path.join(src_folder, str(batch_info['id'])+'.jpg'),
                            os.path.join(dest_folder, str(batch_info['id'])+'.jpg'))
            else:
                os.remove(os.path.join(src_folder, str(batch_info['id'])+'.jpg'))

            # fill Log file
            dict_log["annotation_id"].append(batch_info['id'])
            dict_log["from"].append(src)
            dict_log["to"].append(dest)
            dict_log["who"].append(email)

    # Save Log file
    df = pd.DataFrame.from_dict(dict_log)
    df.to_csv(fname_log, index=False)
    print('\nSaving log file in: {}'.format(fname_log))


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    move_annotations(email=args.email,
                     token=args.token,
                     input_folder=args.ifolder,
                     output_folder=args.ofolder,
                     label_tree_id=args.label_tree_id,
                     src=args.source,
                     dest=args.destination,
                     batch_size=args.batch_size)


if __name__ == "__main__":
    main()
