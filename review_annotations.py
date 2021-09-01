import os
import shutil
import random
import math
import argparse
from datetime import datetime
from tqdm import tqdm
import pandas as pd
from tkinter import Tk, BOTH, Grid, N, E, S, W, Toplevel, IntVar
from tkinter.ttk import Frame, Style, Button
from PIL import ImageTk,Image

from biigle.biigle import Api
import utils as biigle_utils

N_IMG_PER_WND = 9
N_ROWS = N_COLUMNS = int(math.sqrt(N_IMG_PER_WND))
# GUI params
WIDTH_IMG = 200
HEIGTH_IMG = 200
WIDTH_WND = 700
HEIGTH_WND = 600


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')
    mandatory_args.add_argument('-e', '--email', required=True, type=str,
                                help='Email address used for BIIGLE account.')
    mandatory_args.add_argument('-t', '--token', required=True, type=str,
                                help='BIIGLE API token. To generate one: https://biigle.de/settings/tokens')
    mandatory_args.add_argument('-f', '--ifolder', required=True, type=str,
                                help='Input folder, filled with "pull_patches".')
    mandatory_args.add_argument('-i', '--label-tree-id', dest='label_tree_id', required=True, type=int,
                                help='Label tree ID.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-l', '--label-folder', dest='label_folder', required=False, type=str,
                               help='Label folder to review. If indicated, only patches from this folder are reviewed. '
                                    'Otherwise, folders from "-f" are reviewed. If multiple, separate them with '
                                    'commas.')
    optional_args.add_argument('-w', '--window-dims', dest='window_dims', required=False, type=str, default=None,
                               help='Dimensions of images and of the whole window, separated by "x". Default: '
                                    + 'x'.join([str(d) for d in [WIDTH_IMG, HEIGTH_IMG, WIDTH_WND, HEIGTH_WND]]))
    optional_args.add_argument('-n', '--n-patch', dest='n_patches', required=False, type=int,
                               help='Number of patches to review per taxa.')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')

    return parser


class Window(Frame):

    def __init__(self, master, height, width, list_labels):
        super().__init__()
        self.height = height
        self.width = width

        self.master = master

        self.frame = Frame(self.master)
        Grid.rowconfigure(self.master, 0, weight=1)
        Grid.columnconfigure(self.master, 0, weight=1)
        self.frame.grid(row=0, column=0, sticky=N + S + E + W)
        grid = Frame(self.frame)
        grid.grid(sticky=N + S + E + W, column=0, row=7, columnspan=2)
        Grid.rowconfigure(self.frame, 7, weight=1)
        Grid.columnconfigure(self.frame, 0, weight=1)

        self.labelVar = None
        self.changes_list = []

        n_column_buttons = 3
        list_labels.append("NOT_VME")
        n_row_buttons = math.ceil(float(len(list_labels)) / n_column_buttons)
        cmpt_label = 0
        list_btn = []  # creates list to store the buttons ins
        for x in range(n_column_buttons):
            for y in range(n_row_buttons):
                if cmpt_label < len(list_labels):
                    list_btn.append(Button(self.frame, text=list_labels[cmpt_label], command=lambda c=cmpt_label: self.set_label(list_btn[c].cget("text"))))
                    list_btn[cmpt_label].grid(column=x, row=y, sticky=N + S + E + W)
                    cmpt_label += 1

        for x in range(n_column_buttons):
            Grid.columnconfigure(self.frame, x, weight=1)
        for y in range(n_row_buttons):
            Grid.rowconfigure(self.frame, y, weight=1)

        self.accept_key = IntVar()
        self.master.bind("a", self.accept)
        self.master.bind("q", self.quit)
        self.quit_ = False

    def show_img(self, fname_img, taxa):
        self.newWindow = Toplevel(self.master)
        self.sample = Sample(self.newWindow, fname_img, taxa, self.height, self.width)

    def set_label(self, label):
        self.labelVar = label
        self.changes_list = self.changes_list + \
                            [[annotation_id, self.labelVar] for annotation_id in self.sample.annotation_ids]
        self.labelVar = None
        self.sample.annotation_ids = []

    def quit(self, event=None):
        self.accept_key.set(1)
        self.quit_ = True

    def accept(self, event=None):
        self.accept_key.set(1)

    def reset_accept(self, event=None):
        self.accept_key.set(0)
        self.changes_list = []


class Sample:
    def __init__(self, master, fname_img_list, taxa, height, width):
        self.master = master
        self.frame = Frame(self.master,
                           width=width * N_COLUMNS,
                           height=height * N_ROWS)

        self.master.title(taxa)
        self.frame.pack(fill=BOTH, expand=1, side="left")

        # To display on different monitor
        #self.master.wm_geometry("+1500+0")

        self.annotation_ids = []

        Style().configure("TFrame", background="#333")
        image_count = 0
        list_patch = []
        for fname in fname_img_list:
            annotation_id = os.path.split(fname)[1].split('.jpg')[0]
            r, c = divmod(image_count, N_COLUMNS)
            im = Image.open(fname)
            resized = im.resize((height, width), Image.ANTIALIAS)
            tkimage = ImageTk.PhotoImage(resized)
            list_patch.append(Button(self.frame,
                                     image=tkimage,
                                     command=lambda
                                         annotation_id=annotation_id: self.annotation_ids.append(annotation_id)))
            list_patch[image_count].image = tkimage
            list_patch[image_count].grid(row=r, column=c)

            image_count += 1

    def destroy(self):
        self.master.destroy()


def review_annotations(email, token, label_tree_id, input_folder, wnd_dims, n_patches=None, label_folder=[]):
    # Init API
    api = Api(email, token)

    # subfolder list
    if label_folder is None or len(label_folder) == 0:
        taxa_list = [f for f in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, f))]
        print('\nFound {} taxa.'.format(len(taxa_list)))
    else:
        taxa_list = []
        for l in label_folder:
            if os.path.isdir(os.path.join(input_folder, l)):
                taxa_list.append(l)
                print('\nReviewing {}.'.format(os.path.join(input_folder, l)))
            else:
                print('\nFolder not found: {}.'.format(os.path.join(input_folder, l)))
                exit()

    # Get all labels from label tree
    label_tree_info = api.get('label-trees/{}'.format(label_tree_id)).json()['labels']
    label_dict = biigle_utils.get_folders_match_tree(label_tree_info)

    # Log file
    fname_log = os.path.join(input_folder, "logfile_"+datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+".csv")
    dict_log = {"annotation_id": [], "from": [], "to": [], "who": []}

    # Init GUI
    gui = Tk()
    gui.geometry(str(wnd_dims[2]) + "x" + str(wnd_dims[3]) + "+" + str(550) + "+" + str(0))
    # Init main window
    app = Window(master=gui,
                 height=wnd_dims[1],
                 width=wnd_dims[0],
                 list_labels=sorted(list(label_dict.keys())))

    # Loop across taxa
    for taxa in taxa_list:
        print('\nReviewing: {} ...'.format(taxa))
        taxa_folder = os.path.join(input_folder, taxa)
        fname_list = [f for f in os.listdir(taxa_folder) if f.endswith('.jpg')]
        if n_patches is not None and len(fname_list) > n_patches:
            fname_list = random.sample(fname_list, n_patches)
        fname_nested = [fname_list[i:i + N_IMG_PER_WND] for i in range(0, len(fname_list), N_IMG_PER_WND)]

        # Review per chuncks
        for fname_sublist in tqdm(fname_nested, desc="Reviewing"):
            path_list = [os.path.join(taxa_folder, f) for f in fname_sublist]

            # Show image and wait
            app.show_img(path_list, taxa)
            app.wait_variable(app.accept_key)
            # Close window
            app.sample.destroy()
            # Get changes
            change_list = app.changes_list
            # Reset
            app.reset_accept()

            # Loop across changes
            for change in change_list:
                annotation_id, annotation_folder = change

                # Inform about change
                image_id = api.get('image-annotations/{}'.format(annotation_id)).json()['image_id']
                image_info = api.get('images/{}'.format(image_id)).json()
                print('\n\tChange annotation {} from {} to {} on image {} (image ID: {}).'.format(annotation_id,
                                                                                                taxa,
                                                                                                annotation_folder,
                                                                                                image_info['filename'],
                                                                                                image_info['id']))

                # Change label
                if annotation_folder != "NOT_VME":
                    api.post('image-annotations/{}/labels'.format(annotation_id),
                             json={'label_id': label_dict[annotation_folder]['id'],
                                   'confidence': 1})

                # Remove old label
                old_label_id = [ann['id'] for ann in api.get('image-annotations/{}/labels'.format(annotation_id)).json()
                                if ann["label_id"] == label_dict[taxa]['id']][0]
                api.delete('image-annotation-labels/{}'.format(old_label_id))

                # fill Log file
                dict_log["annotation_id"].append(annotation_id)
                dict_log["from"].append(taxa)
                dict_log["to"].append(annotation_folder)
                dict_log["who"].append(email)



                # Move patch folder
                ifname = os.path.join(input_folder, taxa, str(annotation_id)+'.jpg')
                ofname = os.path.join(input_folder, annotation_folder, str(annotation_id)+'.jpg')
                if not os.path.isdir(os.path.join(input_folder, annotation_folder)):
                    os.makedirs(os.path.join(input_folder, annotation_folder))
                shutil.move(ifname, ofname)

            # Quit if asked
            if app.quit_:
                print('\nQuitting the review process.')
                gui.destroy()
                break

        if app.quit_:
            break

    # Quit if not done yet
    if not app.quit_:
        gui.destroy()

    # Save Log file
    df = pd.DataFrame.from_dict(dict_log)
    df.to_csv(fname_log, index=False)
    print('\nSaving log file in: {}'.format(fname_log))


def main():
    parser = get_parser()
    args = parser.parse_args()

    if args.window_dims is None:
        wnd_dims = [WIDTH_IMG, HEIGTH_IMG, WIDTH_WND, HEIGTH_WND]
    else:
        wnd_dims = [int(d) for d in args.window_dims.split('x')]

    # Run function
    review_annotations(email=args.email,
                       token=args.token,
                       label_tree_id=args.label_tree_id,
                       input_folder=args.ifolder,
                       wnd_dims=wnd_dims,
                       n_patches=args.n_patches,
                       label_folder=args.label_folder.split(',') if args.label_folder is not None else [])


if __name__ == "__main__":
    main()