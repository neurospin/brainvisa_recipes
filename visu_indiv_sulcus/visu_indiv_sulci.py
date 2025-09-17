from soma.qt_gui.qt_backend import Qt
import anatomist.api as ana
import os
from soma import aims
from PIL import Image, ImageDraw, ImageFont


def create_grid(image_files, n_cols, out_path, title=None, subject_names=None):
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
    if title or subject_names:
        font = ImageFont.truetype("DejaVuSans.ttf", font_size)
        if title:
            title_h = font.getbbox(title)[3] - font.getbbox(title)[1] + 10  # add margin
        if subject_names:
            legend_h = font.getbbox("Test")[3] - font.getbbox("Test")[1] + 15  # idem

    # create a new blank image with space for title and legend
    grid = Image.new('RGB', (n_cols * w, n_rows * (h + legend_h) + title_h), (255, 255, 255))
    draw = ImageDraw.Draw(grid)

    # Draw title
    if title:
        bbox = draw.textbbox((0, 0), title, font=font)  
        text_w = bbox[2] - bbox[0]
        x = (grid.width - text_w) // 2
        draw.text((x, 5), title, fill=(0, 0, 0), font=font)

    # Paste images and draw subject names
    for idx, im in enumerate(imgs):
        i, j = divmod(idx, n_cols)
        x0 = j * w
        y0 = title_h + i * (h + legend_h)
        grid.paste(im, (x0, y0))

        if subject_names:
            subj = subject_names[idx]
            text_bbox = draw.textbbox((0, 0), subj, font=font)
            text_w = text_bbox[2] - text_bbox[0]
            draw.text((x0 + (w - text_w) // 2, y0 + h-50), subj, fill=(0, 0, 0), font=font)

    grid.save(out_path)
    print(f"Snapshot of the block available at {out_path}")

# select sulcus name, hemisphere, and subjects list
dataset = 'ABCD'  

if dataset == 'dHCP':
    base_dir = (
        '/neurospin/dico/data/human/dHCP/derivatives/release3/morphologist-2023'
    )

else : 
    base_dir = (
        '/neurospin/dico/rmenasria/Runs/03_main/Input/mnt/'
        'soft-brainvisa_ses-baselineYear1Arm1_ver-5.2_morphologist'
    )

SUBJECTS_TEST = ['sub-NDARINVZXPAWB32']
HEMISPHERE = 'R'
#SULCUS_NAME = 'S.T.s._right'  # Trop haut dans la nomenclature, donc colorie trop de sillons
#SULCUS_NAME = 'F.C.M.post._right'  
#SULCUS_NAME = 'F.C.L.p._right'  # F.C.L.p_right est le nom du sulcus dans la nomenclature
#SULCUS_NAMES = ["INSULA_right","F.C.L.p._right"]
SULCUS_NAME = "F.Coll._right"

CAMERA_PARAMS_FCM = {
    'view_quaternion': [-0.26836308836937, -0.323044091463089, -0.315022945404053, -0.851107776165009],
    'zoom': 1.25,
}
CAMERA_PARAMS_STS = {
    'view_quaternion': [-0.506462574005127, 0.718799889087677, 0.241088211536407, -0.410729736089706],
    'zoom': 1.25,
}

CAMERA_PARAMS_FCOLL = {
    'view_quaternion': [0.60460638999939, 0.670526087284088, 0.219961911439896, 0.3694087266922],
    'zoom': 1.25,
}

CAMERA_PARAMS_DEFAULT = {
    'view_quaternion': [0.473252952098846, -0.42669266462326, -0.451164454221725, 0.624832570552826],
    'zoom': 1.25,
}

SUBJECTS_PREMA_CLASSIF_27_32_ABCD_STS= [
    "sub-NDARINV5HH9FDM1",
    "sub-NDARINVN1TKYKW1",
    "sub-NDARINVNBU3UA23",
    "sub-NDARINVDE17JJG5",
    "sub-NDARINVE75NTPTJ",
    "sub-NDARINVJ5VHD38X",
    "sub-NDARINVPPN58EEF",
    "sub-NDARINVM6EBZ88E",
    "sub-NDARINVF41DEHAC",
    "sub-NDARINVTUUTV3B2",
    "sub-NDARINVCCPGPFR1",
    "sub-NDARINVKWBVX0UU",
]

SUBJECTS_PREMA_CLASSIF_27_32_ABCD_FCM = [
    "sub-NDARINV88JX7RKX",
    "sub-NDARINVEWDP96RH",
    "sub-NDARINVGBUMHM8K",
    "sub-NDARINV0GPKYMDC",
    "sub-NDARINVH68T1XNB",
    "sub-NDARINVR28A45T6",
    "sub-NDARINV4YPJW3P2",
    "sub-NDARINVWZRF2GE6",
    "sub-NDARINVCTVENUN4",
    "sub-NDARINVL9NUBDAN",
    "sub-NDARINV0RA4PBPV",
    "sub-NDARINV8KX9UXKE",
]

SUBJECTS_FULLTERMS_CLASSIF_27_32_ABCD_STS = [
    "sub-NDARINVPCCWYX33",
    "sub-NDARINV3BL9Z315",
    "sub-NDARINV1P29RX5F",
    "sub-NDARINVM68WD1CV",
    "sub-NDARINVWPTBB9N7",
    "sub-NDARINV749XW1TD",
    "sub-NDARINVANH9WRCV",
    "sub-NDARINVUN2A7AA5",
    "sub-NDARINV5GB3TA25",
    "sub-NDARINVZR16R6Y3",
    "sub-NDARINVHE58CENN",
    "sub-NDARINV5XJMU584",
]

SUBJECTS_FULLTERMS_CLASSIF_27_32_ABCD_FCM = [
    "sub-NDARINV7XL78LUT",
    "sub-NDARINVE3F19GUV",
    "sub-NDARINV9R3YVGD6",
    "sub-NDARINV5VGKMHCR",
    "sub-NDARINVVUMNAHPB",
    "sub-NDARINVZCDF5310",
    "sub-NDARINVDZLD38UM",
    "sub-NDARINVLZ97FPMY",
    "sub-NDARINV5HNAA4NT",
    "sub-NDARINVUDEPUVAK",
    "sub-NDARINVDUJJ740F",
    "sub-NDARINVLABWKL63",
]


SUBJECTS_PREMA_CLASSIF_27_ABCD_STS = [
    "sub-NDARINVTUUTV3B2",
    "sub-NDARINVV6XHZB59",
    "sub-NDARINVN0XCHU07",
    "sub-NDARINVA4V1CUK7",
    "sub-NDARINVJX8BERDK",
    "sub-NDARINVYZZDEXDF",
    "sub-NDARINV9UL0YHV1",
    "sub-NDARINVNMC8EYAA",
    "sub-NDARINVLFX8PTZ6",
    "sub-NDARINV55285WTD",
    "sub-NDARINVUTBRXV0G",
    "sub-NDARINV14BPGL15",
]


SUBJECTS_PREMA_CLASSIF_27_ABCD_FCM = [
    "sub-NDARINVH68T1XNB",
    "sub-NDARINVNNN5FFAL",
    "sub-NDARINV1KP8VFVR",
    "sub-NDARINV9ZW7Y2R7",
    "sub-NDARINVTZR5RRWU",
    "sub-NDARINVP3B4C2JE",
    "sub-NDARINVYX7ADDMR",
    "sub-NDARINVB1CK69PR",
    "sub-NDARINVVKCT9VLF",
    "sub-NDARINVVD3KF4HE",
    "sub-NDARINVKNBJ47HV",
    "sub-NDARINVFA0DV854",
]


SUBJECTS_FULLTERMS_CLASSIF_27_ABCD_STS = [
    "sub-NDARINV9TZYNDC7",
    "sub-NDARINVBYARCL2L",
    "sub-NDARINVJ46KXBP8",
    "sub-NDARINVDYACTVYF",
    "sub-NDARINVGM7YJH08",
    "sub-NDARINVBZZGY7AM",
    "sub-NDARINVJ8LA1XLG",
    "sub-NDARINVDL871HVM",
    "sub-NDARINV2CVWTNF7",
    "sub-NDARINVM68WD1CV",
    "sub-NDARINVK6W4APWD",
    "sub-NDARINVLMME1BK2",
]


SUBJECTS_FULLTERMS_CLASSIF_27_ABCD_FCM = [
    "sub-NDARINVZJV3HZEF",
    "sub-NDARINVJ51UCKWX",
    "sub-NDARINVLGZ21X0T",
    "sub-NDARINV6R64U2H8",
    "sub-NDARINV8TLTP9PT",
    "sub-NDARINVK2KFJDG5",
    "sub-NDARINVV1LRPT07",
    "sub-NDARINVGGDFBWCL",
    "sub-NDARINVKTEZYKCL",
    "sub-NDARINVRR22WRZJ",
    "sub-NDARINVKZDAJBD7",
    "sub-NDARINVTY7NL56R",
]

SUBJECTS_FULLTERMS_CLASSIF_27_ABCD_STI_STS = [
    "sub-NDARINV4N5LBL4W",
    "sub-NDARINVHE58CENN",
    "sub-NDARINV769BNJY5",
    "sub-NDARINVBZZGY7AM",
    "sub-NDARINVMXMAHBU0",
    "sub-NDARINV8HCVHC17",
    "sub-NDARINVJ8LA1XLG",
    "sub-NDARINVP79AXMBD",
    "sub-NDARINVM68WD1CV",
    "sub-NDARINVR5VKKRM9",
    "sub-NDARINV824JDLTM",
    "sub-NDARINVLMME1BK2"
]

SUBJECTS_PREMA_CLASSIF_27_ABCD_STI_STS = [
    "sub-NDARINVVZJMVTTC",
    "sub-NDARINVJX8BERDK",
    "sub-NDARINV7EZLVXDN",
    "sub-NDARINVTUUTV3B2",
    "sub-NDARINVNVHZ41TU",
    "sub-NDARINVWLNTC8GU",
    "sub-NDARINVFF1W5WM0",
    "sub-NDARINVM2AA5DTD",
    "sub-NDARINVCVAAN2Y5",
    "sub-NDARINVCDNAUD1U",
    "sub-NDARINVCNW0CYU4",
    "sub-NDARINVVA82JDEJ"
]

SUBJECTS_FULLTERMS_CLASSIF_27_32_ABCD_STI_STS = [
    "sub-NDARINV749XW1TD",
    "sub-NDARINVXHYMKR7F",
    "sub-NDARINV11UF2ABG",
    "sub-NDARINV21VH8BF0",
    "sub-NDARINVAYDW5XXV",
    "sub-NDARINVHYTA5DTD",
    "sub-NDARINV29TAPT8B",
    "sub-NDARINVFJLN9GJA",
    "sub-NDARINV67W1B7DK",
    "sub-NDARINVD5ZMXFG6",
    "sub-NDARINV4Z38T1RY",
    "sub-NDARINV0GUTM6AM"
]

SUBJECTS_PREMA_CLASSIF_27_32_ABCD_STI_STS = [
    "sub-NDARINVE1WW821K",
    "sub-NDARINV5HH9FDM1",
    "sub-NDARINVL07PRMYX",
    "sub-NDARINV3BJ59UTE",
    "sub-NDARINVXEKGFN5Y",
    "sub-NDARINVA9H3WMHD",
    "sub-NDARINVN1TKYKW1",
    "sub-NDARINVJ67B8F0J",
    "sub-NDARINVXZ627WWU",
    "sub-NDARINVJ5VHD38X",
    "sub-NDARINVGWJZ3U48",
    "sub-NDARINVDE17JJG5"
]

SUBJECT_SAMPLE_TRUE_FULLTERMS = [
    "sub-NDARINV20KZBB9N",
    "sub-NDARINV20MDTUZ8",
    "sub-NDARINV20MXZPW5",
    "sub-NDARINV20NDWAH8",
    "sub-NDARINV215XKL9U",
    "sub-NDARINV21BW63DB",
    "sub-NDARINV21C5BFGC",
    "sub-NDARINV21CN9606",
    "sub-NDARINV21EBHGF9",
    "sub-NDARINV21YRAN0R",
    "sub-NDARINV21YVF1WJ",
    "sub-NDARINV21ZAXTA3",
    "sub-NDARINV227DRH6R",
    "sub-NDARINV229XUWRH",
    "sub-NDARINV22BFDVEJ",
    "sub-NDARINV22C4YKXN",
    "sub-NDARINV22GRHDPN",
    "sub-NDARINV22VV8H44",
    "sub-NDARINV230CTHZE",
    "sub-NDARINV233UX0N5"
]


SUBJECT_SAMPLE_TRUE_27_32 = [
    "sub-NDARINV26L6B73E",
    "sub-NDARINV26R7MJFV",
    "sub-NDARINV27EPWLDM",
    "sub-NDARINV28B537H0",
    "sub-NDARINV2BPVXTH3",
    "sub-NDARINV2C7F1286",
    "sub-NDARINV2H2UTYYP",
    "sub-NDARINV2H704HJD",
    "sub-NDARINV2J3D85NJ",
    "sub-NDARINV2K2KV0JW",
    "sub-NDARINV2REKB0Y5",
    "sub-NDARINV2V90MWXP"
]

SUBJECT_SAMPLE_TRUE_27 = [
    "sub-NDARINV1ZMY808V",
    "sub-NDARINV3TMCHLA7",
    "sub-NDARINVNY2M953H",
    "sub-NDARINVU102M8W0",
    "sub-NDARINV3TG667EC",
    "sub-NDARINV5UG94F1Y",
    "sub-NDARINV8TCYNPU3",
    "sub-NDARINVCR43W7MR",
    "sub-NDARINVDP1WJ2JC",
    "sub-NDARINVG5XLB72Y",
    "sub-NDARINVLE343UAX",
    "sub-NDARINVLPMG7ZFU"
]

SUBJECTS_PREMA_CLASSIF_27_32_dHCP_STS = [
    "CC00657XX14",
    "CC01038XX16",
    "CC00245BN15",
    "CC00600XX06",
    "CC00955XX15",
    "CC00412XX08",
    "CC00536XX17",
    "CC00152AN04",
    "CC00512XX09",
    "CC00621XX11",
    "CC00747XX22",
    "CC00202XX04"
]

SUBJECTS_PREMA_CLASSIF_27_32_dHCP_STS = [
    "CC00657XX14",
    "CC01038XX16",
    "CC00245BN15",
    "CC00600XX06",
    "CC00955XX15",
    "CC00412XX08",
    "CC00536XX17",
    "CC00152AN04",
    "CC00512XX09",
    "CC00621XX11",
    "CC00747XX22",
    "CC00202XX04"
]

SUBJECTS_FULLTERMS_CLASSIF_27_32_dHCP_STS = [
    "CC00410XX06",
    "CC00268XX13",
    "CC00383XX13",
    "CC01206XX10",
    "CC00131XX08",
    "CC00364XX10",
    "CC00370XX08",
    "CC00091XX10",
    "CC00581XX13",
    "CC00223XX09",
    "CC01194XX16",
    "CC00380XX10",
    "CC00325XX12",
    "CC00080XX07",
    "CC00292XX13",
    "CC00663XX12",
    "CC00357XX11",
    "CC00199XX19",
    "CC00856XX15",
    "CC00852XX11"

]

SUBJECTS_PREMA_CLASSIF_28_32_ABCD__FCLP = [
    "sub-NDARINVUGKWA479",
    "sub-NDARINVK9E4206N",
    "sub-NDARINVA9H3WMHD",
    "sub-NDARINVVZJMVTTC",
    "sub-NDARINV8ZELYTU5",
    "sub-NDARINVCFCXNV7G",
    "sub-NDARINVBF8H4PR1",
    "sub-NDARINV7HLNGBZN",
    "sub-NDARINVBTABKVCU",
    "sub-NDARINVWVFZTJX6",
    "sub-NDARINVTTTWUHHD",
    "sub-NDARINVFC8MZRJA"
]

SUBJECTS_FULLTERMS_CLASSIF_28_32_ABCD__FCLP = [
    "sub-NDARINVEC4FTVA6",
    "sub-NDARINVRH6ZTTH4",
    "sub-NDARINV1JAFHY62",
    "sub-NDARINV2GR8F963",
    "sub-NDARINVAKWF7A8C",
    "sub-NDARINVNYP48E8M",
    "sub-NDARINVMPEAC3HK",
    "sub-NDARINV6U1YT1NL",
    "sub-NDARINV5YLL09V1",
    "sub-NDARINV60X2U63K",
    "sub-NDARINVJVN820EW",
    "sub-NDARINVHJ09MKKG"
]

SUBJECTS_PREMA_CLASSIF_28_32_ABCD_STS = [
    "sub-NDARINVNMJZEZRD",
    "sub-NDARINV9HVP5GZ1",
    "sub-NDARINVEYANDC02",
    "sub-NDARINVBK1CNLJ5",
    "sub-NDARINV3072CP0C",
    "sub-NDARINV27NJ4UJ7",
    "sub-NDARINVFBKHE2PK",
    "sub-NDARINVFF1W5WM0",
    "sub-NDARINVCG8XPP5D",
    "sub-NDARINVF41DEHAC",
    "sub-NDARINVDE17JJG5",
    "sub-NDARINVCFCXNV7G"
]

SUBJECTS_FULLTERMS_CLASSIF_28_32_ABCD_STS= [
    "sub-NDARINVJHUWPMY7",
    "sub-NDARINVTN9RVYB1",
    "sub-NDARINVNDLB4UTU",
    "sub-NDARINVYM29ZAGR",
    "sub-NDARINVMXNTYPJU",
    "sub-NDARINVW482U9L4",
    "sub-NDARINVJXPFFHWU",
    "sub-NDARINVNYP48E8M",
    "sub-NDARINVR57RHGC2",
    "sub-NDARINV9XZMNP0M",
    "sub-NDARINVWPTBB9N7",
    "sub-NDARINVHE58CENN"
]

SUBJECTS_PREMA_CLASSIF_28_32_ABCD_FCM=[
    "sub-NDARINVT3366FHE",
    "sub-NDARINV4VF9CVGF",
    "sub-NDARINV7Z7XV0PB",
    "sub-NDARINV1KP8VFVR",
    "sub-NDARINVY2DXN8WF",
    "sub-NDARINVN6D2HAYA",
    "sub-NDARINVRZL7PGK1",
    "sub-NDARINV5C5YPMZH",
    "sub-NDARINVH68T1XNB",
    "sub-NDARINVCJJ6DH5D",
    "sub-NDARINV7TENJYLH",
    "sub-NDARINVTZR5RRWU"
]


SUBJECTS_FULLTERMS_CLASSIF_28_32_ABCD_FCM = [
    "sub-NDARINV5T572NVH",
    "sub-NDARINV9P7FV88J",
    "sub-NDARINV979TRHXJ",
    "sub-NDARINV2U88LX3T",
    "sub-NDARINVNJJKF0G9",
    "sub-NDARINVXTRHH68Z",
    "sub-NDARINVLM81WCFX",
    "sub-NDARINVZPEYC15U",
    "sub-NDARINV5HNAA4NT",
    "sub-NDARINV5T9K540P",
    "sub-NDARINVLABWKL63",
    "sub-NDARINVDZLD38UM"
]


BEST_RANKED_28_32_COG_LIST = [
    "sub-NDARINVEMTG90C4",
    "sub-NDARINVJLXMB8LP",
    "sub-NDARINVDD40AJMW",
    "sub-NDARINVNC7PM9RJ",
    "sub-NDARINVXAV4KY99",
    "sub-NDARINV50411TBC",
    "sub-NDARINVLEFHD44M",
    "sub-NDARINV1ZMY808V",
    "sub-NDARINVX9YK296T",
    "sub-NDARINV2V90MWXP",
    "sub-NDARINVCR43W7MR",
    "sub-NDARINVWT771AK6"
]

WORST_RANKED_PREMAS_28_32_COG_LIST = [
    "sub-NDARINVM4LX2X19",
    "sub-NDARINVJP9XWZFR",
    "sub-NDARINVKAZ30BTB",
    "sub-NDARINVLE343UAX",
    "sub-NDARINVAB55U5W2",
    "sub-NDARINVBTABKVCU",
    "sub-NDARINVR7WFN9E7",
    "sub-NDARINVR09UG23J",
    "sub-NDARINVACZZH8LM",
    "sub-NDARINVK51MXR7P",
    "sub-NDARINVV5X50ZMM",
    "sub-NDARINVRYT5RRUM"
]



BEST_RANKED_PREMAS_28_32_COGTOTAL = [
    "sub-NDARINVEMTG90C4",
    "sub-NDARINVDD40AJMW",
    "sub-NDARINV2K2KV0JW",
    "sub-NDARINVLEFHD44M",
    "sub-NDARINVXAV4KY99",
    "sub-NDARINVX9YK296T",
    "sub-NDARINVAZL0KJME",
    "sub-NDARINV6KM1LGCB",
    "sub-NDARINV0B7UGM1D",
    "sub-NDARINVDT71ACZT",
    "sub-NDARINV365HAW4K",
    "sub-NDARINVGAKHNMUU"
]

WORST_RANKED_PREMAS_28_32_COGTOTAL= [
    "sub-NDARINV8TCYNPU3",
    "sub-NDARINVR09UG23J",
    "sub-NDARINVR6ET5C77",
    "sub-NDARINV66708YNC",
    "sub-NDARINVJP9XWZFR",
    "sub-NDARINVDP1WJ2JC",
    "sub-NDARINVBW96UH0D",
    "sub-NDARINVA6BFV98B",
    "sub-NDARINV0CRTHE21",
    "sub-NDARINVBW17AA1F",
    "sub-NDARINVK51MXR7P",
    "sub-NDARINVGJFEZAEG"
]

# Scores pour le test de fluidcomp
BEST_RANKED_PREMAS_28_32_COGFLUID= [
    "sub-NDARINVEMTG90C4",
    "sub-NDARINVXAV4KY99",
    "sub-NDARINVAZL0KJME",
    "sub-NDARINVLEFHD44M",
    "sub-NDARINVGAKHNMUU",
    "sub-NDARINVDD40AJMW",
    "sub-NDARINV2V90MWXP",
    "sub-NDARINV9R0Z0T45",
    "sub-NDARINV2K2KV0JW",
    "sub-NDARINVBTVBZ5VX",
    "sub-NDARINVJLXMB8LP",
    "sub-NDARINV5XAZTBUE"
]

WORST_RANKED_PREMAS_28_32_COGFLUID= [
    "sub-NDARINVBTABKVCU",
    "sub-NDARINVF20K5ZNE",
    "sub-NDARINVWNTT8WKJ",
    "sub-NDARINV8TCYNPU3",
    "sub-NDARINVWLJKU8MX",
    "sub-NDARINVBW96UH0D",
    "sub-NDARINVA6BFV98B",
    "sub-NDARINV0CRTHE21",
    "sub-NDARINVACZZH8LM",
    "sub-NDARINV66708YNC",
    "sub-NDARINVBW17AA1F",
    "sub-NDARINVK51MXR7P"
]

# Meilleurs 12 sujets pour le test fluidcomp
BEST_RANKED_FULLTERMS_28_32_COGFLUID = [
    "sub-NDARINV0JWEE23L",
    "sub-NDARINV7DUJG7N2",
    "sub-NDARINV3ZRVGHVN",
    "sub-NDARINV402278X9",
    "sub-NDARINVPGF1DHPJ",
    "sub-NDARINV0PDYPPJ7",
    "sub-NDARINVHJULNANY",
    "sub-NDARINV3XZ29M5N",
    "sub-NDARINVNP2BVPR0",
    "sub-NDARINVC6MPJ7ZF",
    "sub-NDARINVJ7L6EW0J",
    "sub-NDARINVU7WWPJ0M",
]

# Pires 12 sujets pour le test fluidcomp
WORST_RANKED_FULLTERMS_28_32_COGFLUID = [
    "sub-NDARINVFD34548C",
    "sub-NDARINV16PJ1RJ6",
    "sub-NDARINVXWFKM0J5",
    "sub-NDARINVYY9NRYW2",
    "sub-NDARINVP2E79N2K",
    "sub-NDARINVKL523B72",
    "sub-NDARINVP3YKZ978",
    "sub-NDARINVBE0PREAC",
    "sub-NDARINVZZ3P1ZFJ",
    "sub-NDARINVK71MKKBH",
    "sub-NDARINVTY4J79EA",
    "sub-NDARINV2376Z5FY",
]

AVERAGE_RANKED_FULLTERMS_28_32_COGFLUID = [
    "sub-NDARINVZ4LY1E6P",
    "sub-NDARINVRDM1L34M",
    "sub-NDARINVNJA6E3NT",
    "sub-NDARINVPV0GEE35",
    "sub-NDARINVX9YK296T",
    "sub-NDARINVWLDVYXKE",
    "sub-NDARINVZ88J0G50",
    "sub-NDARINVAFBYBN26",
    "sub-NDARINVFBKHE2PK",
    "sub-NDARINVG5XLB72Y",
    "sub-NDARINVKJDAZKWA",
    "sub-NDARINV9JVCWZP3",
]

BEST_RANKED_PREMAS_COGDIR_PICVOCAB = ['sub-NDARINVYFW72521', 'sub-NDARINVXBX1H8JJ', 'sub-NDARINVUFJX48LE', 'sub-NDARINVFLA7T3CM', 'sub-NDARINV3B60KLEU', 'sub-NDARINVEZXL2KXT', 'sub-NDARINVN18KZ8TG', 'sub-NDARINV898CW3V8', 'sub-NDARINVMWH0MZFX', 'sub-NDARINVXPGNE2W4', 'sub-NDARINVNMJZEZRD', 'sub-NDARINVFZ97ZA0Z', 'sub-NDARINVXXKJDH17', 'sub-NDARINVMBU1DVRD', 'sub-NDARINVRTYGC16L', 'sub-NDARINVGB26JEH6']
AVG_RANKED_PREMAS_COGDIR_PICVOCAB = ['sub-NDARINVFD93F59C', 'sub-NDARINVJXT9LVJP', 'sub-NDARINVUAB56Z7Z', 'sub-NDARINVBX3VYZF1', 'sub-NDARINVVA90J10J', 'sub-NDARINV54X5F37C', 'sub-NDARINV905XNJK8', 'sub-NDARINVC4XAJGAN', 'sub-NDARINVN4YXHNL8', 'sub-NDARINVUKG8ND85', 'sub-NDARINVMF00X6VN', 'sub-NDARINVUWTWYGD1', 'sub-NDARINVFR8HM2WT', 'sub-NDARINVHVYT4W45', 'sub-NDARINV112R12P1', 'sub-NDARINVJGGWUMZU']
WORST_RANKED_PREMAS_COGDIR_PICVOCAB = ['sub-NDARINV4HUTD0B9', 'sub-NDARINV32GN03AZ', 'sub-NDARINVDYNUN0GN', 'sub-NDARINV6NR4NZWL', 'sub-NDARINVD3D1K2BX', 'sub-NDARINV5NNKMGJE', 'sub-NDARINVV5HEJ9PA', 'sub-NDARINVZWAPL39H', 'sub-NDARINVWT771AK6', 'sub-NDARINVXWDXTUZ0', 'sub-NDARINVMHC4X2ZU', 'sub-NDARINV8C5PMGAM', 'sub-NDARINV7239K1HB', 'sub-NDARINVLLGNHY2A', 'sub-NDARINVKLT2ZLDF', 'sub-NDARINVF9XMG0N0']


# here select the list 
SUBJECTS = AVG_RANKED_PREMAS_COGDIR_PICVOCAB

app = Qt.QApplication.instance() or Qt.QApplication([])
a = ana.Anatomist()
windows = []
w = a.createWindow('3D')
windows.append(w)
#w.assignReferential(a.centralRef)

if SULCUS_NAME == 'F.C.M.post._right':
        CAMERA_PARAMS = CAMERA_PARAMS_FCM
elif SULCUS_NAME == 'S.T.s._right':
    CAMERA_PARAMS = CAMERA_PARAMS_STS

elif SULCUS_NAME == 'F.Coll._right':
    CAMERA_PARAMS = CAMERA_PARAMS_FCOLL
else:
    CAMERA_PARAMS = CAMERA_PARAMS_DEFAULT 
    
w.camera(
    zoom=CAMERA_PARAMS['zoom'],
    view_quaternion=CAMERA_PARAMS['view_quaternion'],
    force_redraw=True
)


for subj in SUBJECTS:

    if dataset == 'dHCP':
        da = os.path.join(base_dir, f"sub-{subj}",'anat','t1mri',
            'default_acquisition', 'default_analysis')
        mesh_file = os.path.join(
            da, 'segmentation', 'mesh', f"{subj}_{HEMISPHERE}white.gii")
        graph_file = os.path.join(
            da, 'folds', '3.1', 'default_session_auto',f"{HEMISPHERE}{subj}_default_session_auto.arg")
    
    else : 
        da = os.path.join(
            base_dir, subj, 'ses-1', 'anat', 't1mri',
            'default_acquisition', 'default_analysis'
        )

        mesh_file = os.path.join(da, 'segmentation', 'mesh', f"{subj}_{HEMISPHERE}white.gii")

        graph_file = os.path.join(
            da, 'folds', '3.1', 'deepcnn_session_auto',
            f"{HEMISPHERE}{subj}_deepcnn_session_auto.arg"
        )

    mesh = a.loadObject(mesh_file, hidden=False)
    mesh.loadReferentialFromHeader()


    w.addObjects(mesh)
    mesh.setMaterial(a.Material(diffuse=[1, 1, 1, 0.5]))

    graph = a.loadObject(graph_file, hidden=False)
    graph.loadReferentialFromHeader()


    w.addObjects(graph, add_graph_nodes=True)


    hie_path = aims.carto.Paths.findResourceFile('nomenclature/hierarchy/sulcal_root_colors.hie')
    nomenclature = a.loadObject(hie_path)
    
    # Unset the automatic coloring of the graph
    a.execute(
        'GraphDisplayProperties',
        objects=[graph],
        nomenclature_property='plouf'  # does not matter, just to unset the automatic coloring
    )

    # Select from the nomenclature. However, this does not work as expected if the node your want to select as STs for instance has children nodes
    # a.execute(
    #     'SelectByHierarchy',
    #     object=graph,
    #     nomenclature=nomenclature,
    #     names=SULCUS_NAME
    # )
   

    # # Select the sulcus in the graph
    # sf = ana.cpp.SelectFactory.factory()
    # print(f"Selected sulci for {subj}: {sf.selected()}")
    # selected = list(sf.selected()[0])


    # # Set the material for the selected sulcus
    # a.execute('SetMaterial', objects=selected, diffuse=[1.0, 0.35, 0.0, 1.0])
    # If you want to select the sulcus in the graph for Hierachical selection
    #a.execute('Select', unselect_objects=selected)



    # connect to the aim graph object to manually color the sulcus
    aims_graph = graph.graph()
    for vertex in aims_graph.vertices():
        label = vertex.get('label')
        if label == SULCUS_NAME:
            ana_vertex = vertex['ana_object']
            a.execute('SetMaterial', objects=[ana_vertex], diffuse=[1.0, 0.35, 0.0, 1.0])

    
  
    snapshot = True


    # set the camera position

    if snapshot:

        save_dir = "/neurospin/dico/rmenasria/Runs/03_main/Output/Figures/anat_snapshots/cognitive/direction/picvocab/average"
        w.setHasCursor(0)
        fname = f"{subj}_{SULCUS_NAME}.png"
        img_path = os.path.join(save_dir, fname)
        w.snapshot(img_path, width=1200, height=900)

        # Close the window
        #w.close()


    #Remove objects from the window
    #w.removeObjects([mesh, graph, nomenclature])

grid_dir = "/neurospin/dico/rmenasria/Runs/03_main/Output/Figures/anat_snapshots/cognitive/direction/picvocab/average"
create_grid(
    image_files=[
        os.path.join(grid_dir, f"{subj}_{SULCUS_NAME}.png") for subj in SUBJECTS
    ],
    subject_names=SUBJECTS,
    n_cols= 4,
    out_path=os.path.join(
        grid_dir, f"{SULCUS_NAME}_grid.png"),
    title=f"{SULCUS_NAME}"
)


# # Uncomment the following lines if you want to print camera infos periodically in the console. It allows to set manually the camera position in the code above.
# from PyQt5.QtCore import QTimer

# def print_camera_infos():
#     for idx, win in enumerate(windows):
#         try:
#             info = win.getInfos()
#             quat = info.get('view_quaternion', None)
#             zoom = info.get('zoom', None)
#             print(f"Fenêtre {idx} :")
#             print(f"  Quaternion : {quat}")
#             print(f"  Zoom       : {zoom}")
#         except Exception as e:
#             print(f"Erreur pour la fenêtre {idx} : {e}")

# timer = QTimer()
# timer.timeout.connect(print_camera_infos)
# timer.start(5000)



app.exec_()