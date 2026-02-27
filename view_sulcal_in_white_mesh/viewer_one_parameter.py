
"""
View, projected on the mesh, the value of one parameter on the whole brain.

As input, you give a csv file called REGION_VALUES:
- each row is the name of the Champollion_V1 region

"""

#region Imports
# ============================================================
# Imports
# ============================================================

import anatomist.api as ana
from soma.qt_gui.qt_backend import Qt

from PIL import Image

from soma import aims
import numpy as np
import pandas as pd
import glob
import os 

from PIL import ImageFont, ImageDraw, ImageOps

from scipy.ndimage import distance_transform_edt
# endregion

# region Constants
# ============================================================
# Constants and initialization
# ============================================================

a = ana.Anatomist()

# Path to parameter file

# Example of prematurity
REGION_VALUES = "/neurospin/dico/rmenasria/Runs/03_main/Output/final/prematurity/last/ABCD_prematurity_results_final_28_32.csv"
PARAM = "PREMA"
CRITERION = "cv_auc_mean"
CRITERION_DISPLAY = "AUC"
P_VALUE = "perm_pvalue"
REGION_WITHOUT_POINTS = True

## Example of logistic regression with IHI
# path_to_deep_folding = "/neurospin/dico/data/deep_folding/current"
# path_summary = f"{path_to_deep_folding}/models/Champollion_V1_after_ablation/analysis/QTIM"
# path_file = "IHI_QTIM_resid_sex_age.csv"
# REGION_VALUES = f"{path_summary}/{path_file}"
# PARAM = "IHI"
# CRITERION = "auc"
# CRITERION_DISPLAY = "AUC"
# P_VALUE = "p_value"
# REGION_WITHOUT_POINTS = False

THRESHOLD = 0.05/56
MINVAL = 0.5
MAXVAL = None
COEF = 1.02
COMBINE = "MEAN" # "MEAN" # For each vertex, either takes the max (if "MAX") or the mean over the overlapping regions

TITLE = PARAM

SAVE_DIR = "/tmp"
SNAPSHOT = True # if False, plot an anatomist and keep anatomist open, elif True, create a grid, save on file and close anatomist at the end
VERBOSE = False

MNI_ICBM152 = "../disco-6.0/disco_templates_hbp_morpho/icbm152/mni_icbm152_nlin_asym_09c/t1mri/default_acquisition/"
mni_icbm152_nifti_path = aims.carto.Paths.findResourceFile(MNI_ICBM152+"mni_icbm152_nlin_asym_09c.nii.gz")
if not os.path.exists(mni_icbm152_nifti_path):
    print("Check MNI_ICBM152 path, maybe you don't have a v6 version")
mni_icbm152_mesh_path = aims.carto.Paths.findResourceFile(MNI_ICBM152+"default_analysis/segmentation/mesh")
# the masks must be computed again (Be careful with the translation because of the resampling)
# currently using Cristobal's work
MASK_DIR = "/neurospin/dico/cmendoza/Runs/17_PhD_2026/Output/mask_skeleton"
SIDES = ["L", "R"]

# endregion

# region Functions
# ============================================================
# Functions
# ============================================================

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


def get_bounding_box(img, threshold=254):
    # Convert the image to grayscale
    gray_img = ImageOps.grayscale(img)

    # Convert to a binary mask: black for non-white, white for white
    mask = gray_img.point(lambda p: 0 if p > threshold else 255)

    # Find the bounding box of the non-white region
    bbox = mask.getbbox()

    return bbox


def crop_to_bounding_box(img, threshold=254):
    # Get the bounding box
    bbox = get_bounding_box(img, threshold)

    if bbox:
        # Crop the image to the bounding box
        cropped_img = img.crop(bbox)
        return cropped_img
    else:
        # Return the original image if no non-white region is found
        return img
    
    
def zoom_image(source_img, zoom_factor=1.0):
    """
    Returns a zoomed version of source_img.

    Args:
        source_img (Image): The image to zoom and paste.
        zoom_factor (float): The zoom factor (e.g., 2.0 for 2x zoom).
    """
    # Calculate new size after zoom
    new_width = int(source_img.width * zoom_factor)
    new_height = int(source_img.height * zoom_factor)

    # Resize the image
    zoomed_img = source_img.resize((new_width, new_height), Image.LANCZOS)

    return zoomed_img


def align_images_horizontally_centered(images, separator_horizontal):
    """
    Aligns images horizontally, centered vertically.

    Args:
        images (list): List of images.
        separator_horizontal: separator between each image
    """

    # Calculate total width and max height
    total_width = sum(img.width for img in images) + (len(images)-1) * separator_horizontal
    max_height = max(img.height for img in images)

    # Create a new blank image
    combined = Image.new('RGB', (total_width, max_height), (255, 255, 255))

    # Paste each image horizontally, centered vertically
    x_offset = 0
    for img in images:
        # Calculate vertical offset to center the image
        y_offset = (max_height - img.height) // 2
        combined.paste(img, (x_offset, y_offset))
        x_offset += img.width + separator_horizontal

    # Returns the result
    return combined


def stack_images_vertically(image1, image2, separator_vertical):
    # Calculate the total height and the maximum width
    total_height = image1.height + image2.height + separator_vertical
    max_width = max(image1.width, image2.width)

    # Create a new blank image with the calculated dimensions
    new_image = Image.new('RGB', (max_width, total_height),(255, 255, 255))

    # Paste the first image at the top
    new_image.paste(image1, (0, 0))

    # Paste the second image below the first
    new_image.paste(image2, (0, image1.height + separator_vertical))

    return new_image


def match_widths_to_largest(image1, image2):
    # Determine the maximum width
    max_width = max(image1.width, image2.width)

    # Resize the images to match the maximum width
    if image1.width < max_width:
        # Calculate the new height to maintain aspect ratio
        ratio = max_width / image1.width
        new_height = int(image1.height * ratio)
        image1 = image1.resize((max_width, new_height), Image.LANCZOS)

    if image2.width < max_width:
        # Calculate the new height to maintain aspect ratio
        ratio = max_width / image2.width
        new_height = int(image2.height * ratio)
        image2 = image2.resize((max_width, new_height), Image.LANCZOS)

    return image1, image2


def draw_title(grid, title, font):  # ---- Title ----
    if title:
        draw = ImageDraw.Draw(grid)
        bbox = draw.textbbox((0, 0), title, font=font)
        text_w = bbox[2] - bbox[0]
        draw.text(
            ((grid.width - text_w) // 2, 5),
            title,
            fill=(0, 0, 0),
            font=font
        )

def add_vertical_palette_with_ticks_and_labels(
    main_image, palette_image, position,
    tick_positions, labels, criterion,
    tick_length=10, tick_color=(0, 0, 0), label_color=(0, 0, 0), font_size=12):
    """
    Paste a vertical palette image onto a main image with ticks and labels.

    Args:
        main_image: The main image (background).
        palette_image: The vertical palette image to paste.
        position: Tuple (x, y) for the top-left corner of the palette.
        tick_positions: List of relative positions (0-1) for ticks (e.g., [0, 0.25, 0.5, 0.75, 1]).
        labels: List of labels for each tick (e.g., ["0", "25", "50", "75", "100"]).
        tick_length: Length of ticks in pixels.
        tick_color: Color of ticks (RGB).
        label_color: Color of labels (RGB).
        font_size: Font size for labels.

    Returns:
        The combined image with palette, ticks, and labels.
    """
    # Paste the palette image
    main_image.paste(palette_image, position)

    # Create a drawing context
    draw = ImageDraw.Draw(main_image)

    # Load a font
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", font_size)
    except:
        font = ImageFont.load_default()

    # Calculate palette dimensions
    palette_width, palette_height = palette_image.size
    x, y = position

    # Draw ticks and labels
    for i, pos in enumerate(tick_positions):
        # Calculate absolute tick position (vertically)
        if i == (len(tick_positions)-1):
            offset = -5
        else:
            offset = 0    
            
        tick_y = y + int(pos * palette_height) + offset

        # Draw tick (horizontal line to the left of the palette)
        # draw.line([(x - tick_length, tick_y), (x, tick_y)], fill=tick_color, width=1)

        # Get the width of the bounding box of the text
        bbox = draw.textbbox((0, 0), labels[i], font=font)
        width_text = bbox[2] - bbox[0]
        
        # Calculate label position (left of the tick)
        label_x = x - draw.textlength(labels[i], font=font) -5 # - palette_width 
        label_y = tick_y - int(i*font_size)
    
        # Draw label
        draw.text((label_x, label_y), labels[i], fill=label_color, font=font)

    # Get the width of the bounding box of the text
    bbox = draw.textbbox((0, 0), criterion, font=font)
    width_text = bbox[2] - bbox[0]
    height_text = bbox[3] - bbox[1]
    x_title = x - width_text//4
    y_title = y - height_text - 40
    font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 36)
    # Draw title of palette
    draw.text((x_title, y_title), criterion, fill=label_color, font=font_title)

    return main_image


def add_left_right_text(grid, label_color=(0, 0, 0)):
    """Draws L and R text"""
    draw = ImageDraw.Draw(grid)
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 120)
    offset_x = 50
    offset_y = 100
    draw.text((offset_x, offset_y), "L", fill=label_color, font=font)
    draw.text((offset_x, grid.height//2+offset_y), "R", fill=label_color, font=font)
    
    return grid


def create_grid(image_files, n_cols, out_path, title=None, criterion=None,
                palette_path=None, vmin=None, vmax=None):
    global MAXVAL
    zoom_factors = [2, 1.5, 1.5, 2]
    zoom_factors = zoom_factors * 2
    separator_horizontal = 50
    separator_vertical = 10


    # Loads, crops, zooms and matches images
    imgs = [Image.open(f) for f in image_files]
    imgs = [crop_to_bounding_box(img) for img in imgs]
    imgs = [zoom_image(img, zoom_factor) for img, zoom_factor in zip(imgs, zoom_factors)]
    for i in range(n_cols):
        imgs[i], imgs[i+n_cols] = match_widths_to_largest(imgs[i], imgs[i+n_cols])
    
    # Creates grid
    grid_top = align_images_horizontally_centered(imgs[:n_cols], separator_horizontal)
    grid_bottom = align_images_horizontally_centered(imgs[n_cols:], separator_horizontal)
    grid = stack_images_vertically(grid_top, grid_bottom, separator_vertical)

    font_size = 36
    font = ImageFont.truetype("DejaVuSans.ttf", font_size)

    # # ---- Create final canvas ----
    # grid = Image.new(
    #     'RGB',
    #     (sum(widths[:n_cols]), title_h + n_rows * h + palette_h),
    #     (255, 255, 255)
    # )

    draw_title(grid, title, font)
    
    # ---- Palette handling ----
    palette_margin = 20
    if palette_path:
        pal_img = Image.open(palette_path)
        width, height = pal_img.size
        pal_img = pal_img.crop((int(width*vmin), 0, int(width*vmax), height))
        pal_img = pal_img.rotate(90, expand=True)
        pal_w, pal_h = pal_img.size
        x_pal = (grid.width - pal_w) - palette_margin
        y_pal = (grid.height - pal_h) // 2
        
        # Define tick positions (0 to 1) and labels
        # tick_positions = [0, (1.-0.9)/0.5, (1.-0.7)/0.5, 1]
        # labels = ["1.0", "0.9", "0.7", "0.5"]
        tick_positions = [0, 1]
        labels = [str(round(vmax, 2)), str(vmin)]

        # Add the vertical palette with ticks and labels
        grid = add_vertical_palette_with_ticks_and_labels(
            main_image=grid,
            palette_image=pal_img,
            position=(x_pal, y_pal),  # Top-left corner of the palette
            tick_positions=tick_positions,
            labels=labels,
            criterion=criterion,
            tick_length=15,
            tick_color=(0, 0, 0),
            label_color=(0, 0, 0),
            font_size=36
        )
        
        grid = add_left_right_text(grid)

    grid.save(out_path)
    print(f"Snapshot of the block available at {out_path}")

# endregion

# region MainProgram
# ============================================================
# Main program
# ============================================================

def main():
    """Main entry point of the program."""
    global MAXVAL
    
    dic_path = {}
    dic_obj = {}
    dic_window = {}
    dic_tex = {}
    image_files= []

    global_min = np.inf
    global_max = -np.inf

    block = a.createWindowsBlock(4)
    pal = a.createPalette('BR-palette')
    #pal.header()['palette_gradients'] = "0;0.0877193;0.197931;0.197368;0.573103;1;0.764618;1;1;0.385965#0;0;0.242069;0.912281;0.598621;0.872807;0.898621;0.0789474;1;0#0;0.649123;0.590345;0.381579;1;0.0789474#0.5;1"
    # pal.header()['palette_gradients'] = "0;0;0.197931;0.197368;0.573103;1;0.764618;1;0.996885;0.488889;0.996885;1;1;1#0;0;0.242069;0.912281;0.598621;0.872807;0.898621;0.0789474;0.996885;0;0.996885;0.996875;1;1#0;0.711111;0.590345;0.381579;0.996799;0.0888889;0.996799;1;1;1#0.530646;1"
    pal.header()['palette_gradients'] = "0;1;0.00382514;1;0.00382514;0;0.197931;0.197368;0.573103;1;0.764618;1;0.996885;0.488889;0.996885;1;1;1#0;1;0.00437158;1;0.00437158;0;0.242069;0.912281;0.598621;0.872807;0.898621;0.0789474;0.996885;0;0.996885;0.996875;1;1#0;1;0.00382514;1;0.00382514;0.710526;0.590345;0.381579;0.996799;0.0888889;0.996799;1;1;1#0.530646;1"
     
    build_gradient(pal)
    
    df = pd.read_csv(REGION_VALUES)
    
    MAXVAL = df[CRITERION].max()

    df.loc[df[P_VALUE] > THRESHOLD, CRITERION] = 0.5

    print(df.set_index("region")[CRITERION])

    region_value_dict = df.set_index("region")[CRITERION].to_dict()

    for SIDE in SIDES:
        dic_path[f"list_1mm_mask_{SIDE}"] = glob.glob(f"{MASK_DIR}/*/{SIDE}mask_skeleton_1mm.nii.gz")

        dic_window[f"win_{SIDE}_1"] = a.createWindow('3D',
                                    block=block,
                                    no_decoration=True,
                                    options={'hidden': 1})
        dic_window[f"win_{SIDE}_2"] = a.createWindow('3D',
                                    block=block,
                                    no_decoration=True,
                                    options={'hidden': 1})
        dic_window[f"win_{SIDE}_3"] = a.createWindow('3D',
                                    block=block,
                                    no_decoration=True,
                                    options={'hidden': 1})
        dic_window[f"win_{SIDE}_4"] = a.createWindow('3D',
                                    block=block,
                                    no_decoration=True,
                                    options={'hidden': 1})
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
            if REGION_WITHOUT_POINTS:
                region = region.replace('.', '')
            colname = f"{region}_{hemi}"
            
            # colname = region_to_column(region, side, stat=STATISTIC)

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
                if COMBINE == "MAX":
                    value = np.max(value_list[i]) #mean, max
                else:
                    value = np.mean(value_list[i])
                if value <= MINVAL: 
                    # dic_tex[f"tex_{SIDE}"][0][i] = MINVAL
                    dic_tex[f"tex_{SIDE}"][0][i] = COEF * MAXVAL # to use grey palette
                else:
                    dic_tex[f"tex_{SIDE}"][0][i] = value
            else:
                dic_tex[f"tex_{SIDE}"][0][i] = MINVAL # or np.nan or 0.0

        #To have the palette starting from min val
        
        dic_tex[f"tex_{SIDE}"][0][0] = MINVAL # if MINVAL is not None else dic_tex[f"tex_{SIDE}"][0][0]

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
            fill_value = COEF*MAXVAL
            tex_vals[nan_mask] = fill_value

        # Copy values back into the AIMS texture
        for i in range(len(tex_vals)):
            tex[i] = float(tex_vals[i])

        middle_view = [0.5, -0.5, -0.5, 0.5]
        side_view = [0.5, 0.5, 0.5, 0.5]
        bottom_view = [0, -1, 0, 0]
        top_view = [0, 0, 0, -1]

        dic_obj[f"tex_obj_{SIDE}"] = a.toAObject(dic_tex[f"tex_{SIDE}"])
        a.execute("TexturingParams",
                  objects=[dic_obj[f"tex_obj_{SIDE}"]],
                  interpolation="rgb")
        dic_obj[f"fusion_{SIDE}"] = a.fusionObjects([dic_obj[f"tex_obj_{SIDE}"], dic_obj[f"mni_icbm152_{SIDE}mesh_obj"]], "FusionTexSurfMethod")
        dic_obj[f"fusion_{SIDE}"].setPalette('BR-palette', 
                                            minVal=MINVAL, 
                                            maxVal=COEF*MAXVAL)
        if VERBOSE:
            # print(f"min val set to palette at : {MINVAL if MINVAL is not None else None}")
            print(f"Max val set to palette as: {1.01*MAXVAL if MAXVAL is not None else 1.01*global_max}")
            
        # a.setMaterial(dic_obj[f"fusion_{SIDE}"], lighting=0)
        a.setMaterial(
            dic_obj[f"fusion_{SIDE}"],
            lighting=1,
            ambient=[0.4, 0.4, 0.4, 1.0],       # Base plus claire
            diffuse=[0.7, 0.7, 0.7, 1.0],       # Réflexion diffuse plus forte
            emission=[0.1, 0.1, 0.1, 1.0],      # Émission réduite
            specular=[0.2, 0.2, 0.2, 1.0],      # Un peu de brillance
            shininess=10,                        # Légère brillance
            smooth_shading=1
        )
        dic_window[f"win_{SIDE}_1"].addObjects(dic_obj[f"fusion_{SIDE}"])
        dic_window[f"win_{SIDE}_1"].camera(view_quaternion=middle_view if SIDE == "L" else side_view,
                                            zoom=0.5)
        dic_window[f'win_{SIDE}_1'].setHasCursor(0)
        dic_window[f"win_{SIDE}_2"].addObjects(dic_obj[f"fusion_{SIDE}"])
        dic_window[f"win_{SIDE}_2"].camera(view_quaternion=top_view, zoom=0.67)
        dic_window[f'win_{SIDE}_2'].setHasCursor(0)
        dic_window[f"win_{SIDE}_3"].addObjects(dic_obj[f"fusion_{SIDE}"])
        dic_window[f"win_{SIDE}_3"].camera(view_quaternion=bottom_view, zoom=0.67)       
        dic_window[f'win_{SIDE}_3'].setHasCursor(0) 
        dic_window[f"win_{SIDE}_4"].addObjects(dic_obj[f"fusion_{SIDE}"])
        dic_window[f"win_{SIDE}_4"].camera(view_quaternion=side_view if SIDE == "L" else middle_view,
                                            zoom=0.5)
        dic_window[f'win_{SIDE}_4'].setHasCursor(0) 

        if SNAPSHOT:
            if not os.path.exists(SAVE_DIR):
                print(SAVE_DIR, "doesn't exist ! Check your directory.")
            
            path_palette = os.path.join(SAVE_DIR, f"{PARAM}_pal.jpg")
            pal_im = dic_obj[f"fusion_{SIDE}"].palette().toQImage(int(512/(MAXVAL-MINVAL)), 64)
            pal_im.save(path_palette)

            
            PARAM_fname = f"{PARAM}_{SIDE}_view_1.png"
            PARAM_img_path = os.path.join(SAVE_DIR, PARAM_fname)
            dic_window[f'win_{SIDE}_1'].snapshot(PARAM_img_path, width=1250, height=900)
            image_files.append(PARAM_img_path)

            PARAM_fname = f"{PARAM}_{SIDE}_view_2.png"
            PARAM_img_path = os.path.join(SAVE_DIR, PARAM_fname)
            dic_window[f'win_{SIDE}_2'].snapshot(PARAM_img_path, width=1250, height=900)
            image_files.append(PARAM_img_path)
            
            PARAM_fname = f"{PARAM}_{SIDE}_view_3.png"
            PARAM_img_path = os.path.join(SAVE_DIR, PARAM_fname)
            dic_window[f'win_{SIDE}_3'].snapshot(PARAM_img_path, width=1250, height=900)
            image_files.append(PARAM_img_path)

            PARAM_fname = f"{PARAM}_{SIDE}_view_4.png"
            PARAM_img_path = os.path.join(SAVE_DIR, PARAM_fname)
            dic_window[f'win_{SIDE}_4'].snapshot(PARAM_img_path, width=1250, height=900)
            image_files.append(PARAM_img_path)

    if SNAPSHOT:
        create_grid(image_files, 4,f"{SAVE_DIR}/grid_{PARAM}.png",  #f"{SAVE_DIR}/UKB_{PARAM}.png", 
                    title=None, #PARAM
                    criterion=CRITERION_DISPLAY,
                    palette_path=path_palette,
                    vmin= MINVAL,
                    vmax= MAXVAL)
        #a.close()

    else:
        Qt.QApplication.instance().exec_()
# endregion

if __name__ == '__main__':
    main()