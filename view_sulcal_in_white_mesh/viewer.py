import anatomist.api as ana
from soma.qt_gui.qtThread import QtThreadCall
from soma.qt_gui.qt_backend import Qt

a = ana.Anatomist()

from PIL import Image

from soma import aims
import paletteViewer
import numpy as np
import pandas as pd
import glob
import os 

from PIL import Image, ImageFont, ImageDraw

from scipy.ndimage import distance_transform_edt

def erode_mask_mm(vol, erosion_mm=2.0):
    """
    Erode a binary AIMS volume by erosion_mm (in mm).
    """

    # Force true 3D numpy array
    vol_np = np.asarray(vol.np)[..., 0]
    vol_np = np.squeeze(vol_np) > 0

    if vol_np.ndim != 3:
        raise ValueError(f"Expected 3D mask, got shape {vol_np.shape}")

    # Voxel size (XYZ only)
    vs = np.array(vol.header().get('voxel_size', [1, 1, 1]))[:3]

    # Distance transform inside the mask
    dist = distance_transform_edt(vol_np, sampling=vs)

    eroded = dist >= erosion_mm

    # Proper AIMS volume copy
    out = aims.Volume(vol)
    out.np[..., 0] = eroded.astype(out.np.dtype)

    return out

def build_gradient(pal):
    """Build a gradient palette for Anatomist visualization."""
    gw = ana.cpp.GradientWidget(None, 'gradientwidget', pal.header()['palette_gradients'])
    gw.setHasAlpha(True)
    nc = pal.shape[0]
    rgbp = gw.fillGradient(nc, True)
    rgb = rgbp.data()
    npal = pal.np['v']
    pb = np.frombuffer(rgb, dtype=np.uint8).reshape((nc, 4))
    npal[:, 0, 0, 0, :] = pb
    # Convert BGRA to RGBA
    npal[:, 0, 0, 0, :3] = npal[:, 0, 0, 0, :3][:, ::-1]
    pal.update()

def create_grid(image_files, n_cols, out_path, title=None,
                palette_path=None, vmin=None, vmax=None):

    imgs = [Image.open(f) for f in image_files]
    w = max(im.width for im in imgs)
    h = max(im.height for im in imgs)
    n_rows = (len(imgs) + n_cols - 1) // n_cols

    font_size = 36
    font = ImageFont.truetype("DejaVuSans.ttf", font_size)

    title_h = 0
    if title:
        title_h = font.getbbox(title)[3] + 15

    # ---- Palette handling ----
    palette_h = 0
    palette_margin = 20
    if palette_path:
        pal_img = Image.open(palette_path)
        palette_h = pal_img.height + 2 * font_size + palette_margin

    # ---- Create final canvas ----
    grid = Image.new(
        'RGB',
        (n_cols * w, title_h + n_rows * h + palette_h),
        (255, 255, 255)
    )

    draw = ImageDraw.Draw(grid)

    # ---- Paste grid images ----
    for idx, im in enumerate(imgs):
        i, j = divmod(idx, n_cols)
        x0 = j * w
        y0 = title_h + i * h
        grid.paste(im, (x0, y0))

    # ---- Title ----
    if title:
        bbox = draw.textbbox((0, 0), title, font=font)
        text_w = bbox[2] - bbox[0]
        draw.text(
            ((grid.width - text_w) // 2, 5),
            title,
            fill=(0, 0, 0),
            font=font
        )

    # ---- Palette legend ----
    if palette_path:
        pal_w, pal_h = pal_img.size
        x_pal = (grid.width - pal_w) // 2
        y_pal = title_h + n_rows * h + palette_margin

        grid.paste(pal_img, (x_pal, y_pal))

        # min / max labels
        if vmin is not None:
            draw.text(
                (x_pal - 25, y_pal + pal_h + 5),
                f"{vmin:.1f}",
                fill=(0, 0, 0),
                font=font
            )

        if vmax is not None:
            text = f"{vmax:.1f}"
            bbox = draw.textbbox((0, 0), text, font=font)
            draw.text(
                (x_pal + pal_w - bbox[2] - 25, y_pal + pal_h + 5),
                text,
                fill=(0, 0, 0),
                font=font
            )

        nan = True
        if nan is not None:
            text = f"nan"
            bbox = draw.textbbox((0, 0), text, font=font)
            draw.text(
                (x_pal + pal_w - bbox[2] + 55, y_pal + pal_h + 5),
                text,
                fill=(0, 0, 0),
                font=font
            )

    grid.save(out_path)
    print(f"Snapshot of the block available at {out_path}")

def region_to_column(region, side, stat='ZSTAT'):
    hemi = "right" if side == "R" else "left"
    region_clean = region.replace('.', '')
    return f"{region_clean}_{hemi}_{stat}"

def gene_to_region_value_dic(REGION_VALUES, GENE, stat='ZSTAT'):
    region_values = pd.read_csv(REGION_VALUES, sep="\t")
    region_values = region_values[region_values["GENE"] == GENE]
    if region_values.empty:
        raise ValueError(f"Gene '{GENE}' not found in table '{REGION_VALUES}'.")
    region_values = region_values.loc[:, list(region_values.columns.str.endswith(stat))]
    rv = region_values.iloc[0]
    region_value_dict = rv.to_dict()
    return region_value_dict

def csv_to_region_value_dic(REGION_VALUES_CSV):
    region_values = pd.read_csv(REGION_VALUES_CSV)
    region_value_dict = {}
    for index, row in region_values.iterrows(): 
        region_value_dict[row["region"]] = -np.log10(row["p_value"])
    return region_value_dict

MNI_ICBM152 = "../disco-6.0/disco_templates_hbp_morpho/icbm152/mni_icbm152_nlin_asym_09c/t1mri/default_acquisition/"
#REGION_VALUES = "/neurospin/lnao/Champollion/magma_gene_stats_NOPCA_ABCD_All.tsv"
REGION_VALUES = "/neurospin/lnao/Champollion/magma_gene_32PCs.tsv"
REGION_VALUES_CSV = "/home/ad279118/tmp1/all/meta_gencorr_bip_3PCs_summary.csv"
STATISTIC = "ZSTAT"
GENE = "ENSG00000186868"

SAVE_DIR = "/neurospin/dico/adufournet/2026_Nature/images/gene_map"
SNAPSHOT = False
VERBOSE = True
TITLE = GENE
MINVAL = 0
MAXVAL = None


mni_icbm152_nifti_path = aims.carto.Paths.findResourceFile(MNI_ICBM152+"mni_icbm152_nlin_asym_09c.nii.gz")
if not os.path.exists(mni_icbm152_nifti_path):
    print("Check MNI_ICBM152 path, maybe you don't have a v6 version")
mni_icbm152_mesh_path = aims.carto.Paths.findResourceFile(MNI_ICBM152+"default_analysis/segmentation/mesh")
# the masks must be computed again (Be careful with the translation because of the resampling)
# currently using Cristobal's work
MASK_DIR = "/neurospin/dico/cmendoza/Runs/17_PhD_2026/Output/mask_skeleton"
SIDES = ["L", "R"]

list_gene = ["ENSG00000256762", "ENSG00000186868", "ENSG00000120088", "ENSG00000100592", "ENSG00000175745", "ENSG00000260456", "ENSG00000135638", "ENSG00000128573"]

def main():
    for GENE in list_gene:
        if VERBOSE:
            print(GENE)
        region_value_dict = gene_to_region_value_dic(REGION_VALUES, GENE, stat=STATISTIC)
        #region_value_dict = csv_to_region_value_dic(REGION_VALUES_CSV)
        dic_path = {}
        dic_obj = {}
        dic_window = {}
        dic_tex = {}
        image_files= []

        global_min = np.inf
        global_max = -np.inf

        block = a.createWindowsBlock(2)
        pal = a.createPalette('BR-palette')
        #pal.header()['palette_gradients'] = "0;0.0877193;0.197931;0.197368;0.573103;1;0.764618;1;1;0.385965#0;0;0.242069;0.912281;0.598621;0.872807;0.898621;0.0789474;1;0#0;0.649123;0.590345;0.381579;1;0.0789474#0.5;1"
        pal.header()['palette_gradients'] = "0;0;0.197931;0.197368;0.573103;1;0.764618;1;0.996885;0.488889;0.996885;0.644444;1;0.644444#0;0;0.242069;0.912281;0.598621;0.872807;0.898621;0.0789474;0.996885;0;0.996885;0.711111;1;0.666667#0;0.711111;0.590345;0.381579;0.996799;0.0888889;0.996799;0.711111;1;0.711111#0.5;1"
        build_gradient(pal)

        for SIDE in SIDES:
            dic_path[f"list_1mm_mask_{SIDE}"] = glob.glob(f"{MASK_DIR}/*/{SIDE}mask_skeleton_1mm.nii.gz")

            dic_window[f"win_{SIDE}_1"] = a.createWindow('3D',
                                                block=block)
            dic_window[f"win_{SIDE}_2"] = a.createWindow('3D',
                                                block=block)
            path_to_mesh = os.path.join(mni_icbm152_mesh_path, f"mni_icbm152_nlin_asym_09c_{SIDE}white.gii")

            dic_obj[f"mni_icbm152_{SIDE}mesh_obj"] = a.loadObject(path_to_mesh)
            dic_obj[f"mni_icbm152_{SIDE}mesh_obj"].loadReferentialFromHeader()

            icbm152_template = aims.read(path_to_mesh)
            coords = icbm152_template.vertex()
            n_vertices = len(coords)

            if VERBOSE:
                print(list(icbm152_template.header()['referentials']))
                print("Number of vertices:", n_vertices)
                print("First vertex coord:", coords[0])

            #value_sum = np.zeros(n_vertices, dtype=np.float32)
            #value_count = np.zeros(n_vertices, dtype=np.int32)
            value_list = [[] for _ in range(n_vertices)]

            for mask_path in dic_path[f"list_1mm_mask_{SIDE}"]:
                region = mask_path.split('/')[-2]
                side = mask_path.split('/')[-1][0]
                if VERBOSE:
                    print(region)
                

                hemi = "right" if side == "R" else "left"
                region_clean = region.replace('.', '')
                colname = f"{region_clean}_{hemi}"
                
                colname = region_to_column(region, side, stat=STATISTIC)

                if colname not in region_value_dict:
                    print(f"Column not found: {colname}")
                    continue

                region_value = region_value_dict[colname]

                vol = aims.read(mask_path)
                # to erode the masks
                #vol = erode_mask_mm(vol, erosion_mm=1.0)

                vol_ref = vol.header()['referential']
                vol_np = vol.np[..., 0]
                
                dims = np.array(vol.getSize()[:3])
                vals = np.zeros(n_vertices, dtype=np.float32)

                coords_ijk = np.round(coords).astype(int)
                valid = np.all((coords_ijk >= 0) & (coords_ijk < dims), axis=1)
                vals[valid] = vol_np[
                    coords_ijk[valid, 0],
                    coords_ijk[valid, 1],
                    coords_ijk[valid, 2]
                ]
                #hit = vals > 0
                #value_sum[hit] += region_value
                #value_count[hit] += 1

                hit_indices = np.where(vals > 0)[0]
                for idx in hit_indices:
                    value_list[idx].append(region_value)


            dic_tex[f"tex_{SIDE}"] = aims.TimeTexture_FLOAT()
            dic_tex[f"tex_{SIDE}"][0].resize(n_vertices)

            #for i in range(n_vertices):
            #    if value_count[i] > 0:
            #        dic_tex[f"tex_{SIDE}"][0][i] = value_sum[i] / value_count[i]
            #    else:
            #        dic_tex[f"tex_{SIDE}"][0][i] = 0.0  # or np.nan

            for i in range(n_vertices):
                if value_list[i]:
                    dic_tex[f"tex_{SIDE}"][0][i] = np.mean(value_list[i]) #mean, max
                else:
                    dic_tex[f"tex_{SIDE}"][0][i] = np.nan # or np.nan or 0.0

            #To have the palette starting from min val
            dic_tex[f"tex_{SIDE}"][0][0] = MINVAL if MINVAL is not None else dic_tex[f"tex_{SIDE}"][0][0]

            #if VERBOSE:
            #    print("value sum:", value_sum[500:515], "\n")
            #    print("value count:", value_count[500:515], "\n")
            #    print("Vertices with at least one region:",
            #        np.sum(value_count > 0), "/", n_vertices)

            if VERBOSE:
                i = 500
                print(f"Vertex {i} values:", value_list[i])
                print("Mean:", np.mean(value_list[i]) if value_list[i] else None)
                print("Max:",  np.max(value_list[i])  if value_list[i] else None)

            tex_vals = np.asarray(dic_tex[f"tex_{SIDE}"][0])
            valid_vals = tex_vals[tex_vals > 0]

            if valid_vals.size > 0:
                global_min = min(global_min, valid_vals.min())
                global_max = max(global_max, valid_vals.max())

        for SIDE in SIDES:
            tex = dic_tex[f"tex_{SIDE}"][0]
            # Get a NumPy copy
            tex_vals = np.asarray(tex).copy()
            tex_vals = np.asarray(dic_tex[f"tex_{SIDE}"][0])
            nan_mask = np.isnan(tex_vals)

            if nan_mask.any():
                fill_value = 1.1*MAXVAL if MAXVAL is not None else 1.1*global_max
                tex_vals[nan_mask] = fill_value

            # Copy values back into the AIMS texture
            for i in range(len(tex_vals)):
                tex[i] = float(tex_vals[i])

            middle_view = [0.5, -0.5, -0.5, 0.5]
            side_view = [0.5, 0.5, 0.5, 0.5]

            dic_obj[f"tex_obj_{SIDE}"] = a.toAObject(dic_tex[f"tex_{SIDE}"])
            dic_obj[f"fusion_{SIDE}"] = a.fusionObjects([dic_obj[f"tex_obj_{SIDE}"], dic_obj[f"mni_icbm152_{SIDE}mesh_obj"]], "FusionTexSurfMethod")
            dic_obj[f"fusion_{SIDE}"].setPalette('BR-palette', 
                                                minVal=MINVAL if MINVAL is not None else None, 
                                                maxVal=1.01*MAXVAL if MAXVAL is not None else 1.01*global_max,
                                                absoluteMode=True)
            a.setMaterial(dic_obj[f"fusion_{SIDE}"], lighting=0)
            dic_window[f"win_{SIDE}_1"].addObjects(dic_obj[f"fusion_{SIDE}"])
            dic_window[f"win_{SIDE}_1"].camera(view_quaternion=middle_view if SIDE == "L" else side_view)
            dic_window[f"win_{SIDE}_2"].addObjects(dic_obj[f"fusion_{SIDE}"])
            dic_window[f"win_{SIDE}_2"].camera(view_quaternion=side_view if SIDE == "L" else middle_view)

            if SNAPSHOT:
                if not os.path.exists(SAVE_DIR):
                    print(SAVE_DIR, "doesn't exist ! Check your directory.")
                
                path_palette = os.path.join(SAVE_DIR, f"{GENE}_pal.jpg")
                pal_im = dic_obj[f"fusion_{SIDE}"].palette().toQImage(512, 64)
                pal_im.save(path_palette)

                dic_window[f'win_{SIDE}_1'].setHasCursor(0)
                gene_fname1 = f"{GENE}_{SIDE}_view_1.png"
                gene_img_path1 = os.path.join(SAVE_DIR, gene_fname1)
                dic_window[f'win_{SIDE}_1'].snapshot(gene_img_path1, width=1250, height=900)
                image_files.append(gene_img_path1)

                dic_window[f'win_{SIDE}_2'].setHasCursor(0)
                gene_fname2 = f"{GENE}_{SIDE}_view_2.png"
                gene_img_path2 = os.path.join(SAVE_DIR, gene_fname2)
                dic_window[f'win_{SIDE}_2'].snapshot(gene_img_path2, width=1250, height=900)
                image_files.append(gene_img_path2)

        if SNAPSHOT:
            create_grid(image_files,2,f"{SAVE_DIR}/UKB_{GENE}.png",  #f"{SAVE_DIR}/ABCD_all_{GENE}.png", 
                        title=GENE, #GENE
                        palette_path=path_palette,
                        vmin= MINVAL if MINVAL is not None else global_min,
                        vmax= MAXVAL if MAXVAL is not None else global_max)
            #a.close()

        else:
            Qt.QApplication.instance().exec_()

if __name__ == '__main__':
    main()