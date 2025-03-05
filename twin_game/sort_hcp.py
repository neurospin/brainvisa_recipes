#!/usr/bin/env python

import pandas
import numpy as np
import json
import os.path as osp


db_dir = '/neurospin/dico/data/bv_databases/human/not_labeled/hcp'
participants_file = '/neurospin/dico/data/bv_databases/human/not_labeled/hcp/participants.csv'
restricted_file = '/neurospin/dico/jchavas/RESTRICTED_jchavas_1_18_2022_3_17_51.csv'
output_config_file = '/tmp/twin_config.json'


participants = pandas.read_csv(participants_file)
restricted = pandas.read_csv(restricted_file)

mz = restricted[restricted.ZygosityGT == 'MZ']
dz = restricted[restricted.ZygosityGT == 'DZ']
# nt = restricted[restricted.ZygosityGT == ' ']

metadata = {
    "center": "hcp",
    "acquisition": "BL",
    "graph_version": "3.1",
    "sulci_recognition_session": "",
    "under_ses": ""
}

conf = {
    "twin_number": 6,
    "show_sulci": False,
    "dataset": {
        "directory": db_dir,
        "metadata": metadata,
        "twins": {},
        "twin_meta": {}
    }
}

done = set()
num = 0
for tt, tp, mono in (('monozyg', mz, True), ('dizyg', dz, False)):
    tdic = {}
    twins = conf['dataset']['twins']
    tmeta = conf['dataset']['twin_meta']

    for row in range(tp.shape[0]):
        subject = tp.Subject.iloc[row]
        if subject in done:
            continue
        mother = tp.Mother_ID.iloc[row]
        father = tp.Father_ID.iloc[row]
        other = tp[(tp.Mother_ID == mother) & (tp.Father_ID == father)]
        #            & (tp.Age_in_Yrs == tp.Age_in_Yrs.iloc[row])]
        if len(other) != 2:
            print('unmatching twins:', other.Subject)
        else:
            tname = 'twin_%04d' % num
            num += 1
            skip = False
            for s in sorted(other.Subject):
                gmeta = dict(metadata)
                gmeta['subject'] = s
                gmeta['analysis'] = 'default_analysis'
                gmeta['side'] = 'L'
                gname = osp.join(
                    db_dir,
                    '%(center)s/%(subject)s/t1mri/%(acquisition)s/%(analysis)s/folds/%(graph_version)s/%(sulci_recognition_session)s/%(side)s%(subject)s%(under_ses)s.arg' % gmeta)
                if not osp.exists(gname):
                    print('Missing subject files:', s, ':', gname)
                    skip = True
                    break
                gmeta['side'] = 'R'
                gname = osp.join(
                    db_dir,
                    '%(center)s/%(subject)s/t1mri/%(acquisition)s/%(analysis)s/folds/%(graph_version)s/%(sulci_recognition_session)s/%(side)s%(subject)s%(under_ses)s.arg' % gmeta)
                if not osp.exists(gname):
                    print('Missing subject files:', s, ':', gname)
                    skip = True
                    break
            if not skip:
                twins[tname] = [str(x) for x in sorted(other.Subject)]
                tmeta[tname] = {'monozygote': mono}
                p = participants[participants.Subject.isin(other.Subject)]
                if np.all(p.Gender == 'F'):
                    tmeta[tname]['genre'] = 'F'
                elif np.all(p.Gender == 'M'):
                    tmeta[tname]['genre'] = 'M'
                else:
                    tmeta[tname]['genre'] = 'B'
                    if mono:
                        print('WARNING: monozygotes with differing gender !',
                              other)
        done.update(other.Subject)

with open(output_config_file, 'w') as f:
    json.dump(conf, f, indent=4)

