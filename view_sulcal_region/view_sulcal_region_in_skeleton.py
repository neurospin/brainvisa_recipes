from soma.qt_gui.qt_backend import Qt
import anatomist.api as ana
from soma import aims
from soma import aimsalgo

a = ana.Anatomist()

# Variables
_SUBJECT = "100206"
_REGION = "S.C.-sylv."
_SIDE = "R"
_DEEP_FOLDING_BASEDIR = "/neurospin/dico/data/deep_folding/current/datasets/hcp"
_MORPHOLOGIST_BASEDIR = "/neurospin/dico/data/human/hcp/derivatives/morphologist-2023/hcp"
_PATH_TO_WHITEMESH = "t1mri/BL/default_analysis/segmentation/mesh"

# Input file names
mask_icbm_file = f"{_DEEP_FOLDING_BASEDIR}/crops/2mm/{_REGION}/mask/{_SIDE}mask_skeleton.nii.gz"
trm_raw_to_icbm_file = f"{_DEEP_FOLDING_BASEDIR}/transforms/{_SIDE}/{_SIDE}transform_to_ICBM2009c_{_SUBJECT}.trm"
skeleton_raw_file = f"{_DEEP_FOLDING_BASEDIR}/skeletons/raw/{_SIDE}/{_SIDE}skeleton_generated_{_SUBJECT}.nii.gz"
white_mesh_file = f"{_MORPHOLOGIST_BASEDIR}/{_SUBJECT}/{_PATH_TO_WHITEMESH}/{_SUBJECT}_{_SIDE}white.gii"

# We read mask in ICBM 2009 referential, raw skeleton
# and transform from raw referential to ICBM2009
mask_icbm = aims.read(mask_icbm_file)
skeleton_raw = aims.read(skeleton_raw_file)
trm_raw_to_icbm = aims.read(trm_raw_to_icbm_file)
white_mesh_a = a.loadObject(white_mesh_file, hidden=False)


def mesh_and_merge(input_volume):
    # Creates a mesh from the input volume
    mesher = aimsalgo.Mesher()
    mesher.setSmoothing(mesher.LOWPASS, 100, 0.4)
    mesh = mesher.doit(input_volume)
    print(mesh.keys())
    keys = list(mesh.keys())
    key = keys[0]
    print(mesh[key])

    # Merges all meshes into mesh_concat
    mesh_concat = mesh[keys[0]][0]
    for mesh_add in mesh[keys[0]][1:]:
        aims.SurfaceManip.meshMerge(mesh_concat, mesh_add)
    for key in keys[1:]:
        for mesh_add in mesh[key]:
            aims.SurfaceManip.meshMerge(mesh_concat, mesh_add)
    aims.write(mesh_concat, "/tmp/mesh_concat.mesh")

    return mesh_concat


def compute_meshes_sulcal_region(skeleton_raw, mask_icbm, trm_raw_to_icbm):
    # We create a volume mask_raw filled with 0 of the same size 
    # and in the same referential as skeleton_raw
    hdr = skeleton_raw.header()
    dim = hdr['volume_dimension'][:3]
    mask_raw = aims.Volume(dim, dtype='S16')
    mask_raw.copyHeaderFrom(hdr)
    mask_raw.fill(0)

    # Makes the actual resampling of mask_icbm into mask_raw
    # 0 order (nearest neightbours) resampling
    resampler = aimsalgo.ResamplerFactory(mask_icbm).getResampler(0)
    resampler.setRef(mask_icbm)
    resampler.setDefaultValue(0)
    resampler.resample(mask_icbm, trm_raw_to_icbm.inverse(), 0, mask_raw)
    aims.write(mask_raw, "/tmp/mask_raw.nii.gz")

    # Print the headers
    print(f"skeleton_raw header = \n{skeleton_raw.header()}\n")
    print(f"mask_raw header = \n{mask_raw.header()}\n")

    # Closing
    mm = aimsalgo.MorphoGreyLevel_S16()
    skeleton_raw[skeleton_raw.np != 0] = 32767
    closed = mm.doClosing(skeleton_raw, 3.)
    closed = closed.get()

    # Masks the raw skeleton in the raw (native) space with mask_raw
    skeleton_masked = aims.Volume(closed)
    skeleton_masked[mask_raw.np == 0]= 0

    # Mask tha raw skeleton with the negative of the mask
    skeleton_negative_masked = aims.Volume(closed)
    skeleton_negative_masked[mask_raw.np != 0]= 0

    mesh_masked = mesh_and_merge(skeleton_masked)
    mesh_negative_masked = mesh_and_merge(skeleton_negative_masked)

    return mesh_masked, mesh_negative_masked


if __name__ == '__main__':
    mesh_masked, mesh_negative_masked = \
        compute_meshes_sulcal_region(skeleton_raw, mask_icbm, trm_raw_to_icbm)

    # Initialize visualisation
    app = Qt.QApplication.instance()
    if app is None:
        app = Qt.QApplication([])
    w = a.createWindow('3D')
    w.setHasCursor(0)

    # Visualize white mesh
    w.addObjects(white_mesh_a)
    white_mesh_a.setMaterial(a.Material(diffuse=[1.0, 1.0, 1.0, 1.0]))

    # Visualize concatenated meshes
    mesh_masked_a = a.toAObject(mesh_masked)
    w.addObjects(mesh_masked_a)
    mesh_masked_a.setMaterial(a.Material(diffuse=[1.0, 0.35, 0.0, 1.0]))

    mesh_negative_masked_a = a.toAObject(mesh_negative_masked)
    w.addObjects(mesh_negative_masked_a)
    mesh_negative_masked_a.setMaterial(a.Material(diffuse=[0.0, 0., 1.0, 1.0]))

    app.exec_()