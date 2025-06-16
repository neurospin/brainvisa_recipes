"""
Antoine Dufournet

Example of usage:
bv bash

python3 skel_QC.py -p /neurospin/dico/data/deep_folding/current/datasets/ABCD/skeletons \
                   -r raw \
                   -s R \
                   -i /neurospin/dico/data/deep_folding/current/datasets/ABCD/qc.tsv \
                   -n participant_id
"""


import os
import argparse
import multiprocessing
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from multiprocessing import Pool
from soma import aims

multiprocessing.cpu_count()


def get_skeleton_size(subject_id):
    """ 
    Count the number of non negative voxels for a subject, for a given hemisphere.

    Args:
        subject_id (str): for instance 'sub-3459925'
        skeleton_type (str): must be 'raw' or '2mm'
        side (str): must be 'L' or 'R'

    Return:
         subject_id, skeleton_size
    """
    if skeleton_type == 'raw':    
        # To work with the raw skeleton on the /neurospin/dico
        mm_skeleton_path = f'{path_to_skeletons}/raw/{side}'
        skeleton_path = f"{mm_skeleton_path}/{side}skeleton_generated_{subject_id}.nii.gz"

    elif skeleton_type == '2mm':
        mm_skeleton_path = f'{path_to_skeletons}/2mm/{side}'
        skeleton_path = f"{mm_skeleton_path}/{side}resampled_skeleton_{subject_id}.nii.gz"

    else:
        raise "skeleton_type not in list_skeleton_type \n Must be 'raw' or '2mm'"

    if os.path.isfile(skeleton_path):
        skeleton = aims.read(skeleton_path)
        skeleton_size = np.count_nonzero((skeleton.np > 0))

        return subject_id, skeleton_size

    else:
        print(f'{skeleton_path} not found')
        return 0, 0


if __name__ == "__main__":
    # Argument parser setup
    parser = argparse.ArgumentParser(description="Count the number of non negative voxels for a subject, for a given hemisphere.")
    parser.add_argument("-p", "--path", type=str, help="Path to the skeletons folder.")
    parser.add_argument("-r", "--resolution", type=str, choices=["raw", "2mm"], help="Raw or resampled skeleton (raw or 2mm).")
    parser.add_argument("-s", "--side", type=str, choices=["L", "R"], help="Side of the brain (left or right).")
    parser.add_argument("-i", "--pathid", type=str, help="Path to the csv or tsv containing subjects IDs.")
    parser.add_argument("-n", "--IDcolumn", type=str, help="Name of the column with subjects IDs.")

    args = parser.parse_args()

    path_to_skeletons = args.path
    skeleton_type = args.resolution
    side = args.side
    path_sub_id = args.pathid
    IDcolumn = args.IDcolumn

    if path_sub_id.endswith(".csv"):
        sep=','
    elif path_sub_id.endswith(".tsv"):
        sep='\t'
    list_subjects = pd.read_csv(path_sub_id, sep=sep)
    list_subjects = list_subjects[IDcolumn].to_list()

    list_skeleton_size = []
    valid_subjects = []


    with Pool(processes=multiprocessing.cpu_count()) as pool:
        for subject_id, skeleton_size in pool.imap(get_skeleton_size, list_subjects):
            if skeleton_size!=0:
                list_skeleton_size.append(skeleton_size)
                valid_subjects.append(subject_id)
    
    print(len(valid_subjects), len(list_skeleton_size))
    df_skeleton = pd.DataFrame({"ID": valid_subjects, "skeleton_size": list_skeleton_size})

    df_skeleton.to_csv(f'{path_to_skeletons}/{side}_{skeleton_type}_skeleton_size.csv', index=False)

