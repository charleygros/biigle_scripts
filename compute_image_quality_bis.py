import os
import argparse
from tqdm import tqdm
import pandas as pd
from PIL import Image
from datetime import datetime
from skimage.transform import rescale
from ctypes import *

from libsvm import svmutil

import cv2
import numpy as np
import math as m
from scipy.special import gamma as tgamma

ACCEPTED_IMAGE_FORMAT = [".jpg", ".png", ".JPG"]
C_SVC = 0
NU_SVC = 1
ONE_CLASS = 2
EPSILON_SVR = 3
NU_SVR = 4

LINEAR = 0
POLY = 1
RBF = 2
SIGMOID = 3
PRECOMPUTED = 4

# https://github.com/krshrimali/No-Reference-Image-Quality-Assessment-using-BRISQUE-Model/blob/master/Python/brisquequality.py
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


# AGGD fit model, takes input as the MSCN Image / Pair-wise Product
def AGGDfit(structdis):
    # variables to count positive pixels / negative pixels and their squared sum
    poscount = 0
    negcount = 0
    possqsum = 0
    negsqsum = 0
    abssum = 0

    poscount = len(structdis[structdis > 0])  # number of positive pixels
    negcount = len(structdis[structdis < 0])  # number of negative pixels

    # calculate squared sum of positive pixels and negative pixels
    possqsum = np.sum(np.power(structdis[structdis > 0], 2))
    negsqsum = np.sum(np.power(structdis[structdis < 0], 2))

    # absolute squared sum
    abssum = np.sum(structdis[structdis > 0]) + np.sum(-1 * structdis[structdis < 0])

    # calculate left sigma variance and right sigma variance
    lsigma_best = np.sqrt((negsqsum / negcount))
    rsigma_best = np.sqrt((possqsum / poscount))

    gammahat = lsigma_best / rsigma_best

    # total number of pixels - totalcount
    totalcount = structdis.shape[1] * structdis.shape[0]

    rhat = m.pow(abssum / totalcount, 2) / ((negsqsum + possqsum) / totalcount)
    rhatnorm = rhat * (m.pow(gammahat, 3) + 1) * (gammahat + 1) / (m.pow(m.pow(gammahat, 2) + 1, 2))

    prevgamma = 0
    prevdiff = 1e10
    sampling = 0.001
    gam = 0.2

    # vectorized function call for best fitting parameters
    vectfunc = np.vectorize(func, otypes=[np.float], cache=False)

    # calculate best fit params
    gamma_best = vectfunc(gam, prevgamma, prevdiff, sampling, rhatnorm)

    return [lsigma_best, rsigma_best, gamma_best]


def func(gam, prevgamma, prevdiff, sampling, rhatnorm):
    while (gam < 10):
        r_gam = tgamma(2 / gam) * tgamma(2 / gam) / (tgamma(1 / gam) * tgamma(3 / gam))
        diff = abs(r_gam - rhatnorm)
        if (diff > prevdiff): break
        prevdiff = diff
        prevgamma = gam
        gam += sampling
    gamma_best = prevgamma
    return gamma_best


def compute_features(img):
    scalenum = 2
    feat = []
    # make a copy of the image
    im_original = img.copy()

    # scale the images twice
    for itr_scale in range(scalenum):
        im = im_original.copy()
        # normalize the image
        im = im / 255.0

        # calculating MSCN coefficients
        mu = cv2.GaussianBlur(im, (7, 7), 1.166)
        mu_sq = mu * mu
        sigma = cv2.GaussianBlur(im * im, (7, 7), 1.166)
        sigma = (sigma - mu_sq) ** 0.5

        # structdis is the MSCN image
        structdis = im - mu
        structdis /= (sigma + 1.0 / 255)

        # calculate best fitted parameters from MSCN image
        best_fit_params = AGGDfit(structdis)
        # unwrap the best fit parameters
        lsigma_best = best_fit_params[0]
        rsigma_best = best_fit_params[1]
        gamma_best = best_fit_params[2]

        # append the best fit parameters for MSCN image
        feat.append(gamma_best)
        feat.append((lsigma_best * lsigma_best + rsigma_best * rsigma_best) / 2)

        # shifting indices for creating pair-wise products
        shifts = [[0, 1], [1, 0], [1, 1], [-1, 1]]  # H V D1 D2

        for itr_shift in range(1, len(shifts) + 1):
            OrigArr = structdis
            reqshift = shifts[itr_shift - 1]  # shifting index

            # create transformation matrix for warpAffine function
            M = np.float32([[1, 0, reqshift[1]], [0, 1, reqshift[0]]])
            ShiftArr = cv2.warpAffine(OrigArr, M, (structdis.shape[1], structdis.shape[0]))

            Shifted_new_structdis = ShiftArr
            Shifted_new_structdis = Shifted_new_structdis * structdis
            # shifted_new_structdis is the pairwise product
            # best fit the pairwise product
            best_fit_params = AGGDfit(Shifted_new_structdis)
            lsigma_best = best_fit_params[0]
            rsigma_best = best_fit_params[1]
            gamma_best = best_fit_params[2]

            constant = m.pow(tgamma(1 / gamma_best), 0.5) / m.pow(tgamma(3 / gamma_best), 0.5)
            meanparam = (rsigma_best - lsigma_best) * (tgamma(2 / gamma_best) / tgamma(1 / gamma_best)) * constant

            # append the best fit calculated parameters
            feat.append(gamma_best)  # gamma best
            feat.append(meanparam)  # mean shape
            feat.append(m.pow(lsigma_best, 2))  # left variance square
            feat.append(m.pow(rsigma_best, 2))  # right variance square

        # resize the image on next iteration
        im_original = cv2.resize(im_original, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_CUBIC)
    return feat


def genFields(names, types):
	return list(zip(names, types))


class svm_node(Structure):
	_names = ["index", "value"]
	_types = [c_int, c_double]
	_fields_ = genFields(_names, _types)

	def __str__(self):
		return '%d:%g' % (self.index, self.value)


def gen_svm_nodearray(xi, feature_max=None, isKernel=None):
	if isinstance(xi, dict):
		index_range = xi.keys()
	elif isinstance(xi, (list, tuple)):
		if not isKernel:
			xi = [0] + xi  # idx should start from 1
		index_range = range(len(xi))
	else:
		raise TypeError('xi should be a dictionary, list or tuple')

	if feature_max:
		assert(isinstance(feature_max, int))
		index_range = filter(lambda j: j <= feature_max, index_range)
	if not isKernel:
		index_range = filter(lambda j:xi[j] != 0, index_range)

	index_range = sorted(index_range)
	ret = (svm_node * (len(index_range)+1))()
	ret[-1].index = -1
	for idx, j in enumerate(index_range):
		ret[idx].index = j
		ret[idx].value = xi[j]
	max_idx = 0
	if index_range:
		max_idx = index_range[-1]
	return ret, max_idx


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
        dis = cv2.imread(fname, 1)
        # convert to gray scale
        dis = cv2.cvtColor(dis, cv2.COLOR_BGR2GRAY)
        # compute feature vectors of the image
        features = compute_features(dis)
        # rescale the brisqueFeatures vector from -1 to 1
        x = [0]
        # pre loaded lists from C++ Module to rescale brisquefeatures vector to [-1, 1]
        min_ = [0.336999, 0.019667, 0.230000, -0.125959, 0.000167, 0.000616, 0.231000, -0.125873, 0.000165, 0.000600,
                0.241000, -0.128814, 0.000179, 0.000386, 0.243000, -0.133080, 0.000182, 0.000421, 0.436998, 0.016929,
                0.247000, -0.200231, 0.000104, 0.000834, 0.257000, -0.200017, 0.000112, 0.000876, 0.257000, -0.155072,
                0.000112, 0.000356, 0.258000, -0.154374, 0.000117, 0.000351]

        max_ = [9.999411, 0.807472, 1.644021, 0.202917, 0.712384, 0.468672, 1.644021, 0.169548, 0.713132, 0.467896,
                1.553016, 0.101368, 0.687324, 0.533087, 1.554016, 0.101000, 0.689177, 0.533133, 3.639918, 0.800955,
                1.096995, 0.175286, 0.755547, 0.399270, 1.095995, 0.155928, 0.751488, 0.402398, 1.041992, 0.093209,
                0.623516, 0.532925, 1.042992, 0.093714, 0.621958, 0.534484]

        # append the rescaled vector to x
        for i in range(0, 36):
            min = min_[i]
            max = max_[i]
            x.append(-1 + (2.0 / (max - min) * (features[i] - min)))

        # load model
        model = svmutil.svm_load_model("brisque_model/allmodel")
        # create svm node array from python list
        x, idx = gen_svm_nodearray(x[1:], isKernel=(model.param.kernel_type == PRECOMPUTED))
        x[36].index = -1  # set last index to -1 to indicate the end.

        # get important parameters from model
        svm_type = model.get_svm_type()
        is_prob_model = model.is_probability_model()
        nr_class = model.get_nr_class()

        if svm_type in (ONE_CLASS, EPSILON_SVR, NU_SVC):
            # here svm_type is EPSILON_SVR as it's regression problem
            nr_classifier = 1
        dec_values = (c_double * nr_classifier)()

        # calculate the quality score of the image using the model and svm_node_array
        image_quality_score = svmutil.libsvm.svm_predict_probability(model, x, dec_values)

        # Save results
        results_dict["filename"].append(os.path.split(fname)[1])
        results_dict["image_quality_score"].append(image_quality_score)
    print(results_dict)
    exit()
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