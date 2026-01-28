import anatomist.api as ana
from soma.qt_gui.qtThread import QtThreadCall
from soma.qt_gui.qt_backend import Qt

a = ana.Anatomist()

from soma import aims
import numpy as np
import pandas as pd
import glob
import os 

from PIL import Image, ImageFont, ImageDraw

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

def create_grid(image_files, n_cols, out_path, title=None):
    # load all images
    imgs = [Image.open(f) for f in image_files]
    # calculate max width and height
    w = max(im.width for im in imgs)
    h = max(im.height for im in imgs)
    # calculate number of rows
    n_rows = (len(imgs) + n_cols - 1) // n_cols

    title_h = 0
    legend_h = 0
    font_size = 36
    if title:
        font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        if title:
            title_h = font.getbbox(title)[3] - font.getbbox(title)[1] + 10  # add margin

    # create a new blank image with space for title and legend
    grid = Image.new('RGB', (n_cols * w, n_rows * (h + legend_h) + title_h), (255, 255, 255))
    draw = ImageDraw.Draw(grid)

    # Paste images
    for idx, im in enumerate(imgs):
        i, j = divmod(idx, n_cols)
        x0 = j * w
        y0 = title_h + i * (h + legend_h)
        grid.paste(im, (x0, y0))
    # Draw title
    if title:
        bbox = draw.textbbox((0, 0), title, font=font)  
        text_w = bbox[2] - bbox[0]
        x = (grid.width - text_w) // 2
        draw.text((x, 5), title, fill=(0, 0, 0), font=font)

    grid.save(out_path)
    print(f"Snapshot of the block available at {out_path}")

def region_to_column(region, side):
    hemi = "right" if side == "R" else "left"
    region_clean = region.replace('.', '')
    return f"{region_clean}_{hemi}_ZSTAT"

BRAINVISA_ENV = "/volatile/ad279118/brainvisa/.pixi"
MNI_ICBM152 = "envs/default/share/disco-6.0/disco_templates_hbp_morpho/icbm152/mni_icbm152_nlin_asym_09c/t1mri/default_acquisition"
SIDES = ["L", "R"]
REGION_VALUES = "/neurospin/lnao/Champollion/magma_gene_32PCs.tsv"
STATISTIC = "z-score"
GENE = "ENSG00000134250"
SNAPSHOT = True
SAVE_DIR = "/volatile/ad279118/2026_Nature/images/gene_map"
VERBOSE = False

region_values = pd.read_csv(REGION_VALUES, sep="\t")
region_values = region_values[region_values["GENE"] == GENE]
if region_values.empty:
    raise ValueError(f"Gene '{GENE}' not found in table '{REGION_VALUES}'.")
region_values = region_values.loc[:, list(region_values.columns.str.endswith('ZSTAT'))]
rv = region_values.iloc[0]
region_value_dict = rv.to_dict()

mni_icbm152_nifti_path = os.path.join(BRAINVISA_ENV, MNI_ICBM152, "mni_icbm152_nlin_asym_09c.nii.gz")
mni_icbm152_mesh_path = os.path.join(BRAINVISA_ENV, MNI_ICBM152, "default_analysis/segmentation/mesh")

# the masks must be computed again (Be careful with the translation because of the resampling)
# currently using Cristobal's work
MASK_DIR = "/neurospin/dico/cmendoza/Runs/17_PhD_2026/Output/mask_skeleton"


dic_path = {}
dic_obj = {}
dic_window = {}
dic_tex = {}
image_files= []

block = a.createWindowsBlock(2)

for SIDE in SIDES:
    dic_path[f"list_1mm_mask_{SIDE}"] = glob.glob(f"{MASK_DIR}/*/{SIDE}mask_skeleton_1mm.nii.gz")

    dic_window[f"win_{SIDE}_1"] = a.createWindow('3D',
                                        block=block)
    dic_window[f"win_{SIDE}_2"] = a.createWindow('3D',
                                        block=block)
    path_to_mesh = os.path.join(mni_icbm152_mesh_path, f"mni_icbm152_nlin_asym_09c_{SIDE}white.gii")

    dic_obj[f"mni_icbm152_{SIDE}mesh_obj"] = a.loadObject(path_to_mesh)
    dic_obj[f"mni_icbm152_{SIDE}mesh_obj"].loadReferentialFromHeader()
    #dic_window[f"win_{SIDE}"].addObjects(dic_obj[f"mni_icbm152_{SIDE}mesh_obj"])


    icbm152_template = aims.read(path_to_mesh)
    coords = icbm152_template.vertex()
    n_vertices = len(coords)

    if VERBOSE:
        print(list(icbm152_template.header()['referentials']))
        print("Number of vertices:", n_vertices)
        print("First vertex coord:", coords[0])

    value_sum = np.zeros(n_vertices, dtype=np.float32)
    value_count = np.zeros(n_vertices, dtype=np.int32)

    #pal = a.createPalette('VR-palette')
    #pal.header()['palette_gradients'] = "0;0;1;1#1;0.777778#0;0;0;1;1;1#0;0;0.0974359;0.688889;0.5;1;1;0.444444"

    for mask_path in dic_path[f"list_1mm_mask_{SIDE}"]:
        region = mask_path.split('/')[-2]
        side = mask_path.split('/')[-1][0]
        if VERBOSE:
            print(region)
        
        colname = region_to_column(region, side)
        if colname not in region_value_dict:
            print(f"Column not found: {colname}")
            continue

        region_value = region_value_dict[colname]

        vol = aims.read(mask_path)
        vol_ref = vol.header()['referential']
        #a_obj = a.toAObject(vol)
        #a_obj.loadReferentialFromHeader()
        #fusion = a.fusionObjects(objects=[a_obj], method='VolumeRenderingFusionMethod')
        #dic_window[f"win_{SIDE}"].addObjects(fusion)
        #fusion.setPalette('VR-palette', absoluteMode=True)
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
        hit = vals > 0
        value_sum[hit] += region_value
        value_count[hit] += 1


    dic_tex[f"tex_{SIDE}"] = aims.TimeTexture_FLOAT()
    dic_tex[f"tex_{SIDE}"][0].resize(n_vertices)

    for i in range(n_vertices):
        if value_count[i] > 0:
            dic_tex[f"tex_{SIDE}"][0][i] = value_sum[i] / value_count[i]
        else:
            dic_tex[f"tex_{SIDE}"][0][i] = 0.0  # or np.nan if you prefer
    if VERBOSE:
        print("value sum:", value_sum[500:515], "\n")
        print("value count:", value_count[500:515], "\n")
        print("Vertices with at least one region:",
            np.sum(value_count > 0), "/", n_vertices)

    middle_view = [0.5, -0.5, -0.5, 0.5]
    side_view = [0.5, 0.5, 0.5, 0.5]

    dic_obj[f"tex_obj_{SIDE}"] = a.toAObject(dic_tex[f"tex_{SIDE}"])
    dic_obj[f"fusion_{SIDE}"] = a.fusionObjects([dic_obj[f"tex_obj_{SIDE}"], dic_obj[f"mni_icbm152_{SIDE}mesh_obj"]], "FusionTexSurfMethod")
    dic_window[f"win_{SIDE}_1"].addObjects(dic_obj[f"fusion_{SIDE}"])
    dic_window[f"win_{SIDE}_1"].camera(view_quaternion=middle_view if SIDE == "L" else side_view)
    dic_window[f"win_{SIDE}_2"].addObjects(dic_obj[f"fusion_{SIDE}"])
    dic_window[f"win_{SIDE}_2"].camera(view_quaternion=side_view if SIDE == "L" else middle_view)

    if SNAPSHOT:
        if not os.path.exists(SAVE_DIR):
            print(SAVE_DIR, "doesn't exist ! Check your directory.")

        dic_window[f'win_{SIDE}_1'].setHasCursor(0)
        gene_fname1 = f"{GENE}_{side}_view_1.png"
        gene_img_path1 = os.path.join(SAVE_DIR, gene_fname1)
        dic_window[f'win_{SIDE}_1'].snapshot(gene_img_path1, width=1250, height=900)
        image_files.append(gene_img_path1)

        dic_window[f'win_{SIDE}_2'].setHasCursor(0)
        gene_fname2 = f"{GENE}_{side}_view_2.png"
        gene_img_path2 = os.path.join(SAVE_DIR, gene_fname2)
        dic_window[f'win_{SIDE}_2'].snapshot(gene_img_path2, width=1250, height=900)
        image_files.append(gene_img_path2)

create_grid(image_files,2,f"{SAVE_DIR}/grid_{GENE}.png", title=GENE)

Qt.QApplication.instance().exec_()
