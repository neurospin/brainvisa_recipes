# %% [markdown]
# This notebook displays on the SPAM model of sulci the value of the parameter for each sulcus. The entry point is a dictionary containing the value to plot for each sulcus.
# 
# Requires anatomist from the BrainVISA software suite

# %% [markdown]
# # 1. Imports 

# %%
import anatomist.api as anatomist
from soma.qt_gui.qtThread import QtThreadCall
from soma.qt_gui.qt_backend import Qt

# %%
from soma import aims
import os
import subprocess
import pandas as pd

from PIL import Image, ImageFont, ImageDraw, ImageOps

# %% [markdown]
# # 2. Paths and constants

# %%
diff_data = {
    "F.I.P._right": -7.15, "S.T.s._right": -4.67, "F.C.L.p._right": 0.00,
    "INSULA_right": -2.27, "OCCIPITAL_right": -12.11, "S.C._right": -7.20,
    "S.F.sup._right": -6.50, "S.F.inter._right": -3.67, "F.Cal.ant.-Sc.Cal._right": -0.86,
    "S.T.i.post._right": -5.88, "F.P.O._right": -1.64, "F.Coll._right": -8.04,
    "F.C.M.post._right": -1.50, "F.C.M.ant._right": 1.05, "S.F.inf._right": -0.62,
    "F.I.P.Po.C.inf._right": -13.67, "S.T.s.ter.asc.post._right": -5.11,
    "S.T.i.ant._right": -1.79, "S.F.int._right": 1.04, "S.T.s.ter.asc.ant._right": -6.79,
    "S.Call._right": -2.64, "S.Pe.C.inter._right": -4.96, "S.Or._right": 0.63,
    "S.O.T.lat.post._right": -6.51, "S.O.T.lat.ant._right": -0.87, "S.Pa.int._right": -3.57,
    "S.Pe.C.inf._right": -12.08, "S.s.P._right": -4.34, "S.T.pol._right": 5.30,
    "S.F.polaire.tr._right": -3.38, "S.Olf._right": -4.16, "S.Po.C.sup._right": -14.82,
    "S.R.sup._right": -12.59, "S.F.marginal._right": -3.72, "S.F.inf.ant._right": 1.69,
    "S.F.median._right": 0.69, "S.Pe.C.sup._right": -12.23, "S.Pa.t._right": -8.65,
    "S.Cu._right": -1.84, "F.C.L.r.asc._right": -6.95, "S.Pa.sup._right": -2.10,
    "S.O.T.lat.med._right": 1.81, "F.C.L.r.ant._right": -13.66, "S.Pe.C.marginal._right": -0.86,
    "S.Li.post._right": -10.77, "S.Rh._right": -13.94, "F.C.L.r.retroC.tr._right": 6.29,
    "S.Pe.C.median._right": 4.05, "S.O.p._right": 0.07, "S.p.C._right": 0.65
}

PARAMETER = "CLASSIF"
param = "diff_data"

defaultVal = -20
minVal = -15
maxVal = 15

SNAPSHOT = False


# %%
SIDE = 'R'

learnclean_path = aims.carto.Paths.findResourceFile("models/models_2008/descriptive_models/segments")

# %%
# Gets SPAM models on which visualization is done
Rspam_model = aims.carto.Paths.findResourceFile(
    "models/models_2008/descriptive_models/"
    "segments/global_registered_spam_right/meshes/Rspam_model_meshes_0.arg")
# Rspam_model = f"{mni_icbm152_graph_path}/Rmni_icbm152_nlin_asym_09c_default_session_2_manual.arg"
Lspam_model = aims.carto.Paths.findResourceFile(
    "models/models_2008/descriptive_models/segments/"
    "global_registered_spam_left/meshes/Lspam_model_meshes_0.arg")

# %%
Rspam_model

# %% [markdown]
# # 2. Preprocessing

# %%
res = pd.DataFrame.from_dict(diff_data, orient="index", columns = [param])
res.index.name = "sulcus"
res = res.reset_index()
res[param] *= -1
res.head()

# %% [markdown]
# # 3. Anatomist functions

# %%
def set_color_property(res, side):
    global dic_window
    global param

    # Element to bring the smoothed white mesh and apply the resuired transformation into Talairach
    side_long = "right" if side == "R" else "left"
    path_to_mesh = os.path.join(learnclean_path, f"global_registered_spam_{side_long}/meshes/{side}white_spam.gii")
    path_to_trm = os.path.join(learnclean_path, f"global_registered_spam_left/meshes/Lwhite_TO_global_spam.trm")
    path_to_mesh_trm = f"/tmp/{side}white_spam_transformed.gii"
    result = subprocess.run(["AimsApplyTransform", "-i", path_to_mesh, "-o", path_to_mesh_trm, "-m", path_to_trm], capture_output=True, text=True)
    # Print the output
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
    
    dic_window[f"aimslearnclean{side}"] = aims.read(path_to_mesh_trm)

    if side == "L":
        dic_window[f"aims{side}"] = aims.read(Lspam_model)
        dic_window[f"aims{side}"]['boundingbox_min'][0] = 0
    else:
        dic_window[f"aims{side}"] = aims.read(Rspam_model)
        dic_window[f"aims{side}"]['boundingbox_max'][0] = 0

    for vertex in dic_window[f"aims{side}"].vertices():
        vertex[param] = defaultVal
    print(f"param = {param}")
        
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
                vertex[param] = row[param]
                
    untouched_vertices = []
    for vertex in dic_window[f"aims{side}"].vertices():
        vname = vertex.get('name')
        if vertex[param] == defaultVal:
            #print(f"Removing vertex with name: {name}")
            untouched_vertices.append(vertex)
            
    # So that minVal is captured
    for vertex in untouched_vertices:
        # dic_window[f"aims{side}"].removeVertex(vertex)
        vertex[param] = minVal
    
    # dic_window[f"anamesh{side}"] = a.loadObject(path_to_mesh)
    # dic_window[f"anamesh{side}"].loadReferentialFromHeader()
    
    dic_window[f"ana{side}"] = a.toAObject(dic_window[f"aims{side}"])
    dic_window[f"analearnclean{side}"] = a.toAObject(dic_window[f"aimslearnclean{side}"] )

    dic_window[f"ana{side}"].setColorMode(dic_window[f"ana{side}"].PropertyMap)
    dic_window[f"ana{side}"].setColorProperty(param)
    dic_window[f"ana{side}"].notifyObservers()
    
    # So that minVal is captured
    for vertex in untouched_vertices:
        dic_window[f"aims{side}"].removeVertex(vertex)
    
                
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
    dic_window[f"win{i}"].addObjects(dic_window[f"analearnclean{side}"])
    dic_window[f"win{i}"].addObjects(dic_window[f"ana{side}"])
    
    # Trick to save the palette with the extrema colors
    dic_window[f"ana{side}"].setPalette("bwr")
    pal_im = dic_window[f"ana{side}"].palette().toQImage(256, 32)  # 256 x 32 est la taille que tu veux
    pal_im.save(f'/tmp/pal{i}.jpg')
    
    dic_window[f"ana{side}"].setPalette("bwr",
                              minVal=minVal, maxVal=maxVal,
                              absoluteMode=True)
    
    dic_window[f"win{i}"].camera(view_quaternion=view_quaternion)
    dic_window[f"win{i}"].setHasCursor(0)
    
    if SNAPSHOT:
        image_file = f"/tmp/snapshot{i}.jpg"
        dic_window[f"win{i}"].snapshot(image_file,
                                width=1250,
                                height=900)
        return image_file
    else:
        return ""
        

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


def add_left_right_text(grid, label_color=(0, 0, 0)):
    """Draws L and R text"""
    draw = ImageDraw.Draw(grid)
    font = ImageFont.truetype("DejaVuSans-Bold.ttf", 120)
    offset_x = 50
    offset_y = 100
    draw.text((offset_x, offset_y), "L", fill=label_color, font=font)
    draw.text((offset_x, grid.height//2+offset_y), "R", fill=label_color, font=font)
    
    return grid


def create_grid(image_files, n_cols, one_line, out_path, title=None, criterion=None,
                palette_path=None, vmin=None, vmax=None):

    # zoom_factors = [1, 1.5, 1.5, 1]
    zoom_factors = [1, 1]
    zoom_factors = zoom_factors * 2
    separator_horizontal = 50
    separator_vertical = 10


    # Loads, crops, zooms and matches images
    imgs = [Image.open(f) for f in image_files]
    imgs = [crop_to_bounding_box(img) for img in imgs]
    imgs = [zoom_image(img, zoom_factor) for img, zoom_factor in zip(imgs, zoom_factors)]
    n_rows = (len(imgs) + n_cols - 1) // n_cols
    h = max(im.height for im in imgs)
    
    
    if not one_line:
        for i in range(n_cols):
            imgs[i], imgs[i+n_cols] = match_widths_to_largest(imgs[i], imgs[i+n_cols])
    
    # Creates grid
    grid_top = align_images_horizontally_centered(imgs[:n_cols], separator_horizontal)
    if one_line:
        grid = grid_top
    else:
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
    title_h = 0
    
    # ---- Palette handling ----
    palette_margin = 20
    if palette_path:
        palette_h = 0
        palette_margin = 20
        if palette_path:
            pal_img = Image.open(palette_path)
            pal_img = pal_img.transpose(Image.FLIP_LEFT_RIGHT)
        
        if not one_line:
            grid = add_left_right_text(grid)

    draw = ImageDraw.Draw(grid)

    # ---- Palette legend ----
    if palette_path:
        pal_w, pal_h = pal_img.size
        x_pal = (grid.width - pal_w) // 2
        y_pal = title_h + n_rows * h - 2*palette_margin

        grid.paste(pal_img, (x_pal, y_pal))

        draw.text(
            (grid.width//2-15, y_pal - pal_h - 5),
            "0",
            fill=(0, 0, 0),
            font=font
        )

        # min / max labels
        if vmin is not None:
            draw.text(
                (x_pal - 60, y_pal-5),
                f"{vmin}",
                fill=(0, 0, 0),
                font=font
            )

        if vmax is not None:
            text = f"{vmax}"
            bbox = draw.textbbox((0, 0), text, font=font)
            draw.text(
                (x_pal + pal_w - bbox[2] + 50, y_pal-5),
                text,
                fill=(0, 0, 0),
                font=font
            )

        nan = None
        if nan is not None:
            text = f"nan"
            bbox = draw.textbbox((0, 0), text, font=font)
            draw.text(
                (x_pal + pal_w - bbox[2] + 55, y_pal - pal_h - 5),
                text,
                fill=(0, 0, 0),
                font=font
            )
            
    grid.save(out_path)
    print(f"Snapshot of the block available at {out_path}")


def visualize_whole(res, side, start):
    set_color_property(res, side)
    first_img = visualize_whole_hemisphere(middle_view if side == "L" else side_view, side, start+0)
    second_img = visualize_whole_hemisphere(top_view, side, start+1)
    third_img = visualize_whole_hemisphere(bottom_view, side, start+2)
    fourth_img = visualize_whole_hemisphere(side_view if side == "L" else middle_view, side, start+3)
    return [first_img, second_img, third_img, fourth_img]


def visualize_two(res, side, start):
    set_color_property(res, side)
    first_img = visualize_whole_hemisphere(side_view if side == "L" else middle_view, side, start+1)
    # second_img = visualize_whole_hemisphere(top_view, side, start+1)
    # third_img = visualize_whole_hemisphere(bottom_view, side, start+2)
    fourth_img = visualize_whole_hemisphere(middle_view if side == "L" else side_view, side, start+0)
    return [first_img, fourth_img]

# %% [markdown]
# # Main function

# %%
a = anatomist.Anatomist()

# %% [markdown]
# 

# %%


# %%
middle_view = [0.5, -0.5, -0.5, 0.5]
side_view = [0.5, 0.5, 0.5, 0.5]
bottom_view = [0, -1, 0, 0]
top_view = [0, 0, 0, -1]

# %%
# %matplotlib qt5

# %%
dic_window = {} # Global dictionary of windows
# left_images = visualize_whole(res, "L", 0)
left_images = []
right_images = visualize_two(res, "R", 0)
image_files = left_images + right_images

# %%


# %%
if SNAPSHOT:
    create_grid(
        image_files, 2, True, f"/tmp/grid_SPAM_{PARAMETER}.png", title=None,
        criterion="", palette_path=f'/tmp/pal0.jpg',
        vmin=minVal,
        vmax=maxVal)
else:
    Qt.QApplication.instance().exec_()

# %%


# %%



