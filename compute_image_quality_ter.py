import os
import argparse
from tqdm import tqdm
import pandas as pd
from PIL import Image
from datetime import datetime
import imquality.brisque as brisque

ACCEPTED_IMAGE_FORMAT = [".jpg", ".png", ".JPG"]

# https://github.com/ocampor/image-quality
# python compute_image_quality_ter.py -i R:\IMAS\Antarctic_Seafloor\Clean_Data_For_Permanent_Storage\AA2011\AA2011_3_colourcorrected_images_for_annotation -o iqs_aa2011


def get_parser():
    parser = argparse.ArgumentParser(add_help=False)

    # MANDATORY ARGUMENTS
    mandatory_args = parser.add_argument_group('MANDATORY ARGUMENTS')
    mandatory_args.add_argument('-i', '--input', required=True, type=str,
                                help='Input, either image filename or folder. If folder, all images contained in this '
                                     'folder will be processed. Accepted formats: PNG, JPG.')

    # OPTIONAL ARGUMENTS
    optional_args = parser.add_argument_group('OPTIONAL ARGUMENTS')
    optional_args.add_argument('-o', '--output-folder', dest='output_folder', required=False, type=str, default='.',
                               help='Output folder where the results are saved, in a csv file. If this folder does not '
                                    'exist yet, it will be created.')
    optional_args.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS,
                               help='Shows function documentation.')

    return parser


def is_image(fname):
    for f_format in ACCEPTED_IMAGE_FORMAT:
        if fname.endswith(f_format):
            return True
    return False


def compute_image_quality(input_path, output_path, tmp_path=None, survey_name=None):
    print("PyPI")
    # Get image paths
    image_list = []
    if is_image(input_path):
        image_list.append(input_path)
    else:
        if os.path.isdir(input_path):
            for i_fname in os.listdir(input_path):
                if is_image(i_fname):
                    image_list.append(os.path.join(input_path, i_fname))

    # Throw error if no image found
    if not len(image_list):
        print("No image found in: "+input_path)
        print("Accepted image formats: {}".format(ACCEPTED_IMAGE_FORMAT))
        exit()
    else:
        print("Found {} images.".format(len(image_list)))

    # Create output folder if does not exist yet
    if not os.path.isdir(output_path):
        os.makedirs(output_path)

    # Load tmp
    if tmp_path is None:
        tmp_path = os.path.join(output_path, "results_"+survey_name+"_tmp.csv")
        fname_done_list = []
        results_dict = {"filename": [], "image_quality_score": []}
    else:
        tmp_df = pd.read_csv(tmp_path)
        fname_done_list = tmp_df['filename'].tolist()
        results_dict = {"filename": tmp_df['filename'].tolist(),
                        "image_quality_score": tmp_df['image_quality_score'].tolist()}

    # Loop
    for fname in tqdm(image_list, desc="Computing image quality score"):
        tail = os.path.split(fname)[1]
        if tail in fname_done_list:
            continue
        img = Image.open(fname)
        image_quality_score = brisque.score(img)

        # Save results
        results_dict["filename"].append(tail)
        results_dict["image_quality_score"].append(image_quality_score)
        pd.DataFrame.from_dict(results_dict).to_csv(tmp_path, index=False)
    print(results_dict)

    # Save final results
    o_fname = os.path.join(output_path, "results_"+datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+".csv")
    results_pd = pd.DataFrame.from_dict(results_dict).sort_values(by='image_quality_score')
    results_pd.to_csv(o_fname, index=False)
    print("\nFinal results saved in: {}".format(o_fname))

    return o_fname

def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    compute_image_quality(input_path=args.input,
                          output_path=args.output_folder)


if __name__ == "__main__":
    main()