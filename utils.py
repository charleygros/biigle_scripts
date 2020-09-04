

def get_folders_match_tree(label_tree_info):
    out_dict = {}
    for label_info in label_tree_info:
        parent_info = [label_tree_info_ for label_tree_info_ in label_tree_info
                       if label_tree_info_['id'] == label_info['parent_id']]

        if len(parent_info) == 0:  # No parent
            parent_name = ''
            key_name = label_info['name'].replace(' ', '_')
        elif len(parent_info) == 1:
            parent_name = parent_info[0]['name']
            key_name = parent_name.replace(' ', '_') + '-' + label_info['name'].replace(' ', '_')
        else:
            print('ERROR: multiple parents: {}.'.format(label_info))
            exit()

        out_dict[key_name] = label_info

    return out_dict
