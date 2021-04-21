import os
import argparse
from tqdm import tqdm
import pandas as pd
from PIL import Image
from datetime import datetime
import numpy as np
import scipy.signal as signal
import scipy.special as special
import scipy.optimize as optimize
from skimage.transform import rescale
import collections
from itertools import chain
import pickle
from libsvm import svmutil

ACCEPTED_IMAGE_FORMAT = [".jpg", ".png", ".JPG"]

# python compute_image_quality.py -i R:\IMAS\Antarctic_Seafloor\Clean_Data_For_Permanent_Storage\AA2011\AA2011_3_colourcorrected_images_for_annotation -o iqs_aa2011


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


def normalize_kernel(kernel):
    return kernel / np.sum(kernel)


def gaussian_kernel2d(n, sigma):
    Y, X = np.indices((n, n)) - int(n/2)
    gaussian_kernel = 1 / (2 * np.pi * sigma ** 2) * np.exp(-(X ** 2 + Y ** 2) / (2 * sigma ** 2))
    return normalize_kernel(gaussian_kernel)


def local_mean(image, kernel):
    return signal.convolve2d(image, kernel, 'same')


def local_deviation(image, local_mean, kernel):
    "Vectorized approximation of local deviation"
    sigma = image ** 2
    sigma = signal.convolve2d(sigma, kernel, 'same')
    return np.sqrt(np.abs(local_mean ** 2 - sigma))


def calculate_mscn_coefficients(image, kernel_size=6, sigma=7 / 6):
    C = 1 / 255
    kernel = gaussian_kernel2d(kernel_size, sigma=sigma)
    local_mean = signal.convolve2d(image, kernel, 'same')
    local_var = local_deviation(image, local_mean, kernel)

    return (image - local_mean) / (local_var + C)


def generalized_gaussian_dist(x, alpha, sigma):
    beta = sigma * np.sqrt(special.gamma(1 / alpha) / special.gamma(3 / alpha))

    coefficient = alpha / (2 * beta() * special.gamma(1 / alpha))
    return coefficient * np.exp(-(np.abs(x) / beta) ** alpha)


def calculate_pair_product_coefficients(mscn_coefficients):
    return collections.OrderedDict({
        'mscn': mscn_coefficients,
        'horizontal': mscn_coefficients[:, :-1] * mscn_coefficients[:, 1:],
        'vertical': mscn_coefficients[:-1, :] * mscn_coefficients[1:, :],
        'main_diagonal': mscn_coefficients[:-1, :-1] * mscn_coefficients[1:, 1:],
        'secondary_diagonal': mscn_coefficients[1:, :-1] * mscn_coefficients[:-1, 1:]
    })


def asymmetric_generalized_gaussian(x, nu, sigma_l, sigma_r):
    def beta(sigma):
        return sigma * np.sqrt(special.gamma(1 / nu) / special.gamma(3 / nu))

    coefficient = nu / ((beta(sigma_l) + beta(sigma_r)) * special.gamma(1 / nu))
    f = lambda x, sigma: coefficient * np.exp(-(x / beta(sigma)) ** nu)

    return np.where(x < 0, f(-x, sigma_l), f(x, sigma_r))


def asymmetric_generalized_gaussian_fit(x):
    def estimate_phi(alpha):
        numerator = special.gamma(2 / alpha) ** 2
        denominator = special.gamma(1 / alpha) * special.gamma(3 / alpha)
        return numerator / denominator

    def estimate_r_hat(x):
        size = np.prod(x.shape)
        return (np.sum(np.abs(x)) / size) ** 2 / (np.sum(x ** 2) / size)

    def estimate_R_hat(r_hat, gamma):
        numerator = (gamma ** 3 + 1) * (gamma + 1)
        denominator = (gamma ** 2 + 1) ** 2
        return r_hat * numerator / denominator

    def mean_squares_sum(x, filter=lambda z: z == z):
        filtered_values = x[filter(x)]
        squares_sum = np.sum(filtered_values ** 2)
        return squares_sum / ((filtered_values.shape))

    def estimate_gamma(x):
        left_squares = mean_squares_sum(x, lambda z: z < 0)
        right_squares = mean_squares_sum(x, lambda z: z >= 0)

        return np.sqrt(left_squares) / np.sqrt(right_squares)

    def estimate_alpha(x):
        r_hat = estimate_r_hat(x)
        gamma = estimate_gamma(x)
        R_hat = estimate_R_hat(r_hat, gamma)

        solution = optimize.root(lambda z: estimate_phi(z) - R_hat, [0.2]).x

        return solution[0]

    def estimate_sigma(x, alpha, filter=lambda z: z < 0):
        return np.sqrt(mean_squares_sum(x, filter))

    def estimate_mean(alpha, sigma_l, sigma_r):
        return (sigma_r - sigma_l) * constant * (special.gamma(2 / alpha) / special.gamma(1 / alpha))

    alpha = estimate_alpha(x)
    sigma_l = estimate_sigma(x, alpha, lambda z: z < 0)
    sigma_r = estimate_sigma(x, alpha, lambda z: z >= 0)

    constant = np.sqrt(special.gamma(1 / alpha) / special.gamma(3 / alpha))
    mean = estimate_mean(alpha, sigma_l, sigma_r)

    return alpha, mean, sigma_l, sigma_r


def calculate_brisque_features(image, kernel_size=7, sigma=7 / 6):
    def calculate_features(coefficients_name, coefficients, accum=np.array([])):
        alpha, mean, sigma_l, sigma_r = asymmetric_generalized_gaussian_fit(coefficients)

        if coefficients_name == 'mscn':
            var = (sigma_l ** 2 + sigma_r ** 2) / 2
            return [alpha, var]

        return [alpha, mean, sigma_l ** 2, sigma_r ** 2]

    mscn_coefficients = calculate_mscn_coefficients(image, kernel_size, sigma)
    coefficients = calculate_pair_product_coefficients(mscn_coefficients)

    features = [calculate_features(name, coeff) for name, coeff in coefficients.items()]
    flatten_features = list(chain.from_iterable(features))
    return np.array(flatten_features)


def scale_features(features):
    with open('brisque_model/normalize.pickle', 'rb') as handle:
        scale_params = pickle.load(handle)

    min_ = np.array(scale_params['min_'])
    max_ = np.array(scale_params['max_'])

    return -1 + (2.0 / (max_ - min_) * (features - min_))


def calculate_image_quality_score(brisque_features):
    model = svmutil.svm_load_model('brisque_model/brisque_svm.txt')
    #scaled_brisque_features = scale_features(brisque_features)
    scaled_brisque_features = brisque_features

    x, idx = svmutil.gen_svm_nodearray(
        scaled_brisque_features,
        isKernel=(model.param.kernel_type == svmutil.PRECOMPUTED))

    nr_classifier = 1
    prob_estimates = (svmutil.c_double * nr_classifier)()

    return svmutil.libsvm.svm_predict_probability(model, x, prob_estimates)


def compute_image_quality(input_path, output_path):
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

    results_dict = {"filename": [], "image_quality_score": []}
    for fname in tqdm(image_list, desc="Computing image quality score"):
        # Load image as grayscale
        img = np.array(Image.open(fname).convert('L'))
        # Fit Coefficients to Generalized Gaussian Distributions
        brisque_features = calculate_brisque_features(img, kernel_size=7, sigma=7/6)
        # Resize Image and Calculate BRISQUE Features
        w, h = img.shape
        downscaled_image = rescale(img, scale=1/2, order=3)
        downscale_brisque_features = calculate_brisque_features(downscaled_image, kernel_size=7, sigma=7 / 6)
        brisque_features = np.concatenate((brisque_features, downscale_brisque_features))
        # Scale Features and Feed the SVR
        image_quality_score = calculate_image_quality_score(brisque_features)

        # Save results
        results_dict["filename"].append(os.path.split(fname)[1])
        results_dict["image_quality_score"].append(image_quality_score)

    # Save final results
    o_fname = os.path.join(output_path, "results_"+datetime.now().strftime("%Y-%m-%d_%H-%M-%S")+".csv")
    results_pd = pd.DataFrame.from_dict(results_dict).sort_values(by='image_quality_score')
    results_pd.to_csv(o_fname, index=False)
    print("\nFinal results saved in: {}".format(o_fname))


def main():
    parser = get_parser()
    args = parser.parse_args()

    # Run function
    compute_image_quality(input_path=args.input,
                          output_path=args.output_folder)


if __name__ == "__main__":
    main()