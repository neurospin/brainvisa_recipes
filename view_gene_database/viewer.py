"""
python viewer.py \
    -d /home/ad279118/tmp1/MAGMA/magma_gene_stats_32PCs.tsv \
    -g ENSG00000171634 \
    -s ZSTAT \
    -r filtered_region_to_sulci.json
"""

import anatomist.api as anatomist
from soma.qt_gui.qtThread import QtThreadCall
from soma.qt_gui.qt_backend import Qt

from soma import aims
import pandas as pd
import numpy as np
import scipy.stats
import argparse
import scipy
import json
import glob
import sys
import os

a = anatomist.Anatomist()


def get_sulci(region):
    """
    Parameters
    ----------
    region : str
        The name of the brain region (e.g., "SFint-FCMant_left").

    Returns
    -------
    list or None
        A list of sulcus names associated with the region, or None if the region is not found.    
    """
    global filtered_region_to_sulci
    if region in filtered_region_to_sulci.keys():
        list_sulci = list(filtered_region_to_sulci[region])
        return list_sulci
    else:
        print(f"{region} not in filtered_region_to_sulci keys.")
        return None

def get_gene(genes_rslt, gene_id, statistic):
    """
    Extracts regional statistics for a specific gene and maps regions to corresponding sulci.

    This function locates the row corresponding to the provided gene (using either SYMBOL or GENE ID)
    from a DataFrame of gene statistics. It then reshapes the regional values for the chosen statistic 
    ('ZSTAT' or 'P'), and determines the associated sulci for each region using the `get_sulci` function.

    Parameters
    ----------
    genes_rslt : pd.DataFrame
        DataFrame containing gene-level statistics across brain regions. Must include columns
        'SYMBOL', 'GENE', and region-specific columns like `REGION_left_ZSTAT`, `REGION_right_P`, etc.
        
    gene_id : str
        The gene identifier, which can be either a gene SYMBOL or ENSEMBL GENE ID.
        
    statistic : str
        The statistic to extract for each region. Should be either 'ZSTAT' or 'P'.
        
    Returns
    -------
    pd.DataFrame
        A DataFrame with one row per region, containing:
        - 'region_type': original column name with region and statistic (e.g., 'OCCIPITAL_left_ZSTAT')
        - statistic: the corresponding statistic value
        - 'region': the extracted region name (e.g., 'OCCIPITAL_left')
        - 'side': the hemisphere side ('left' or 'right')
        - 'sulcus': a list of sulci corresponding to the region (via `get_sulci`)
        
    Raises
    ------
    ValueError
        If the specified gene is not found in the input DataFrame.
    """
    row = genes_rslt[(genes_rslt['SYMBOL'] == gene_id) | (genes_rslt['GENE'] == gene_id)]

    if row.empty:
        raise ValueError(f"Gene {gene_id} not found in data.")

    row = row.iloc[0]
    long = row.filter(like=f'_{statistic}').reset_index()
    long.columns = ['region_type', statistic]

    long['region'] = long['region_type'].str.replace(f'_{statistic}$', '', regex=True)
    long['side'] = long['region'].str.extract(r'_(left|right)')[0].str.lower()
        
    # Get sulci list
    long['sulcus'] = long.apply(lambda x: get_sulci(x.region), axis=1)
    return long

def get_stat_per_sulcus(long, statistic):
    """
    Returns a clean DataFrame mapping each sulcus to a region, hemisphere side, and statistic.

    Parameters
    ----------
    long : pd.DataFrame
        DataFrame returned by `get_gene()`, containing columns:
        - 'region_type': original region/statistic label
        - 'ZSTAT' or 'P': the statistic of interest
        - 'region': simplified region name
        - 'side': hemisphere side ('left' or 'right')
        - 'sulcus': list of sulci associated with the region
    
    statistic : str
        The statistic to extract for each region. Should be either 'ZSTAT' or 'P'.

    Returns
    -------
    pd.DataFrame
        A DataFrame where each row corresponds to one sulcus, with columns:
        - 'region': the region it was assigned to
        - 'side': hemisphere ('left' or 'right')
        - 'sulcus': the sulcus name
        - statistic: the statistical value associated with the region

    """
    df_exploded = long.explode("sulcus").copy()
    df_exploded = df_exploded.dropna()
    
    print(df_exploded)

    return df_exploded

def set_color_property(res, side, statistic):
    global dic_window

    if side == "L":
        spam_model_file = Lspam_model
    else:
        spam_model_file = Rspam_model
        
    dic_window[f"aims{side}"] = aims.read(spam_model_file)

    for vertex in dic_window[f"aims{side}"].vertices():
        vertex[statistic] = 0.


    unknown_vertices = []
    for vertex in dic_window[f"aims{side}"].vertices():
        vname = vertex.get('name')
        if vname == 'unknown':
            #print(f"Removing vertex with name: {name}")
            unknown_vertices.append(vertex)
    for vertex in unknown_vertices:
        dic_window[f"aims{side}"].removeVertex(vertex)


    for _, row in res.iterrows():
        for vertex in dic_window[f"aims{side}"].vertices():
            vname = vertex.get('name')
            if vname == row.sulcus:

                if statistic == 'ZSTAT':
                    vertex[statistic] = row[statistic]

                if statistic == 'P':
                    vertex[statistic] = -np.log10(row[statistic])
                
    
    dic_window[f"ana{side}"] = a.toAObject(dic_window[f"aims{side}"])

    dic_window[f"ana{side}"].setColorMode(dic_window[f"ana{side}"].PropertyMap)
    dic_window[f"ana{side}"].setColorProperty(statistic)
    dic_window[f"ana{side}"].notifyObservers()
    
                
def visualize_whole_hemisphere(view_quaternion, side, i):
    global block
    global dic_window
    try:
        block
    except NameError:
        block = a.createWindowsBlock(4)

    dic_window[f"win{i}"] = a.createWindow('3D',
                                    block=block,
                                    no_decoration=True,
                                    options={'hidden': 1})
    dic_window[f"win{i}"].addObjects(dic_window[f"ana{side}"])
    dic_window[f"ana{side}"].setPalette("green_yellow_red",
                              minVal=0,
                              absoluteMode=True)
    
    dic_window[f"win{i}"].camera(view_quaternion=view_quaternion)

    # 0;1;0.579487;1;0.992308;1#0;1;0.246154;0.822222;0.630769;0.311111;1;0#0;1;0.320513;0.0888889;1;0#0.5;1

def visualize_whole(res, side, start):
    set_color_property(res, side, statistic)
    visualize_whole_hemisphere(middle_view if side == "L" else side_view, side, start+0)
    visualize_whole_hemisphere(top_view, side, start+1)
    visualize_whole_hemisphere(bottom_view, side, start+2)
    visualize_whole_hemisphere(side_view if side == "L" else middle_view, side, start+3)


Rspam_model = "/casa/host/build/share/brainvisa-share-5.2/models/models_2008/descriptive_models/segments/global_registered_spam_right/meshes/Rspam_model_meshes_1.arg"
if not os.path.exists(Rspam_model):
    Rspam_model = "/volatile/ad279118/brainvisa/.pixi/envs/default/share/brainvisa-share-6.0/models/models_2008/descriptive_models/segments/global_registered_spam_right/meshes/Rspam_model_meshes_1.arg"
Lspam_model = "/casa/host/build/share/brainvisa-share-5.2/models/models_2008/descriptive_models/segments/global_registered_spam_left/meshes/Lspam_model_meshes_1.arg"
if not os.path.exists(Lspam_model):
    Lspam_model ="/volatile/ad279118/brainvisa/.pixi/envs/default/share/brainvisa-share-6.0/models/models_2008/descriptive_models/segments/global_registered_spam_left/meshes/Lspam_model_meshes_1.arg"

middle_view = [0.5, -0.5, -0.5, 0.5]
side_view = [0.5, 0.5, 0.5, 0.5]
bottom_view = [0, -1, 0, 0]
top_view = [0, 0, 0, -1]
dic_window = {}

def main():
    global filtered_region_to_sulci, statistic

    # -- Parse arguments --
    parser = argparse.ArgumentParser(description="Visualize gene statistics on sulci via Anatomist.")
    parser.add_argument("-d", "--database", type=str, required=True,
                        help="Path to the TSV file with gene statistics (MAGMA output).")
    parser.add_argument("-g", "--gene", type=str, required=True,
                        help="Gene identifier (SYMBOL or ENSEMBL ID).")
    parser.add_argument("-s", "--statistic", type=str, choices=['ZSTAT', 'P'], default='ZSTAT',
                        help="Statistic to visualize (ZSTAT or P).")
    parser.add_argument("-r", "--region_to_sulci", type=str, required=True,
                        help="Path to JSON file mapping regions to sulci.")
    args = parser.parse_args()

    # -- Load data --
    with open(args.region_to_sulci) as f:
        filtered_region_to_sulci = json.load(f)

    filtered_region_to_sulci = {
        k.replace('.', ''): v
        for k, v in filtered_region_to_sulci.items()
    }

    genes_rslt = pd.read_csv(args.database, sep='\t')
    statistic = args.statistic

    # -- Compute --
    long = get_gene(genes_rslt, args.gene, statistic)
    df_sulcus = get_stat_per_sulcus(long, statistic)

    # -- Visualize --
    visualize_whole(df_sulcus, "L", 0)
    visualize_whole(df_sulcus, "R", 4)

    # -- Keep UI alive --
    Qt.QApplication.instance().exec_()

if __name__ == "__main__":
    main()