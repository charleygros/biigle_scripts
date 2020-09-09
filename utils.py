

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


def clean_df(df, list_image_id):
    # Get columns of interest
    df = df[['label_hierarchy', 'image_id', 'filename', 'shape_name', 'points',
                                           'attributes']]
    # Rename labels
    df['label_hierarchy'] = df['label_hierarchy'].str.replace(' > ', '-')
    df['label_hierarchy'] = df['label_hierarchy'].str.replace(' ', '_')
    # Get image filenames of interest
    if list_image_id:
        list_image_fname = df[df['image_id'].isin(df)]['filename'].unique().tolist()
    else:
        list_image_fname = df['filename'].unique().tolist()
    print('\n{} images selected.'.format(len(list_image_fname)))
    # Keep images of interest
    df_biigle = df[df['filename'].isin(list_image_fname)]
    # Get CoralNet filename
    df_biigle['filename'] = df_biigle['filename'].str.split("__", expand=True)[1].str.split(".jpg", expand=True)[0]

    return df
