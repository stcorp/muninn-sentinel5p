import os
import re
from datetime import datetime, timedelta

from muninn.struct import Struct
from muninn.schema import Mapping, Text, Integer
from muninn.geometry import Point, LinearRing, Polygon


# Namespaces

class Sentinel5PNamespace(Mapping):
    file_class = Text(index=True)
    file_type = Text(index=True)
    orbit = Integer(index=True, optional=True)
    collection = Integer(index=True, optional=True)
    processor_version = Integer(index=True, optional=True)


def namespaces():
    return ['s5p']


def namespace(name):
    return Sentinel5PNamespace


# Product types

L1_PRODUCT_TYPES = [
    'L1B_RA_BD1',
    'L1B_RA_BD2',
    'L1B_RA_BD3',
    'L1B_RA_BD4',
    'L1B_RA_BD5',
    'L1B_RA_BD6',
    'L1B_RA_BD7',
    'L1B_RA_BD8',
    'L1B_IR_UVN',
    'L1B_IR_SIR',
    'L1B_CA_UVN',
    'L1B_CA_SIR',
    'L1B_ENG_DB',
]

L2_PRODUCT_TYPES = [
    'L2__AER_AI',
    'L2__AER_LH',
    'L2__CH4___',
    'L2__CLOUD_',
    'L2__CO____',
    'L2__FRESCO',
    'L2__HCHO__',
    'L2__NO2___',
    'L2__NP_BD3',
    'L2__NP_BD6',
    'L2__NP_BD7',
    'L2__O3_TCL',
    'L2__O3_TPR',
    'L2__O3__PR',
    'L2__O3____',
    'L2__SO2___',
]

AUX_PRODUCT_TYPES = [
    'AUX_CTMANA',
    'AUX_CTMCH4',
    'AUX_CTMFCT',
    'AUX_CTM_CO',
    'AUX_ISRF__',
    'AUX_MET_2D',
    'AUX_MET_QP',
    'AUX_MET_TP',
    'AUX_NISE__',
    'AUX_O3PPWL',
    'AUX_O3___M',
    'AUX_SF_UVN',
    'CFG_AER_AI',
    'CFG_AER_LH',
    'CFG_CH4__F',
    'CFG_CH4___',
    'CFG_CO___F',
    'CFG_CO____',
    'CFG_FRESCB',
    'CFG_FRESCO',
    'CFG_NO2___',
    'CFG_O3_PRF',
    'CFG_O3__PR',
    'LUT_AAI___',
    'LUT_ALH_NN',
    'LUT_CH4AER',
    'LUT_CH4CIR',
    'LUT_FRESCO',
    'LUT_NO2AMF',
    'LUT_NO2CLD',
    'LUT_O22CLD',
    'LUT_O3PCLD',
    'LUT_O3PPOL',
    'LUT_POLCOR',
    'REF_DEM___',
    'REF_LER___',
    'REF_SOLAR_',
    'REF_XS_CH4',
    'REF_XS_NO2',
    'REF_XS_O3P',
    'REF_XS__CO',
]

MUNINN_PRODUCT_TYPES = []

for _type in L1_PRODUCT_TYPES + L2_PRODUCT_TYPES + AUX_PRODUCT_TYPES:
    MUNINN_PRODUCT_TYPES.append("S5P_" + _type)


def get_footprint(product):
    try:
        import coda
    except ImportError:
        return None
    path = "/METADATA/EOP_METADATA/om_featureOfInterest/eop_multiExtentOf/gml_surfaceMembers/gml_exterior@gml_posList"
    pf = coda.open(product)
    try:
        coord = coda.fetch(pf, path).split(' ')
    except coda.CodacError:
        return None
    finally:
        coda.close(pf)
    if len(coord) % 2 != 0:
        return None
    return Polygon([LinearRing([Point(float(lon), float(lat)) for lat, lon in zip(coord[0::2], coord[1::2])])])


class Sentinel5PProduct(object):

    def __init__(self, product_type):
        self.product_type = product_type
        # see https://earth.esa.int/web/sentinel/user-guides/sentinel-5p-tropomi/naming-convention
        pattern = [
            r"S5P",
            r"(?P<file_class>.{4})",
            r"(?P<file_type>%s)" % product_type[4:],  # e.g. "S5P_L2__NO2___" -> "L2__NO2___"
            r"(?P<validity_start>[\dT]{15})",
            r"(?P<validity_stop>[\dT]{15})",
            r"(?P<orbit>.{5})",
            r"(?P<collection>.{2})",
            r"(?P<processor_version>.{6})",
            r"(?P<creation_date>[\dT]{15})"
        ]
        self.filename_pattern = "_".join(pattern) + r"\.nc$"

    @property
    def namespaces(self):
        return ["s5p"]

    @property
    def use_enclosing_directory(self):
        return False

    @property
    def use_hash(self):
        # For compatibility with muninn versions before 5.1
        return True

    @property
    def hash_type(self):
        return "md5"

    def parse_filename(self, filename):
        match = re.match(self.filename_pattern, os.path.basename(filename))
        if match:
            return match.groupdict()
        return None

    def identify(self, paths):
        if len(paths) != 1:
            return False
        return re.match(self.filename_pattern, os.path.basename(paths[0])) is not None

    def archive_path(self, properties):
        name_attrs = self.parse_filename(properties.core.physical_name)
        validity_start = properties.core.validity_start
        return os.path.join(
            "sentinel-5p",
            name_attrs['file_type'],
            name_attrs['file_class'],
            validity_start.strftime("%Y"),
            validity_start.strftime("%m"),
            validity_start.strftime("%d")
        )

    def analyze(self, paths, filename_only=False):
        inpath = paths[0]
        name_attrs = self.parse_filename(inpath)

        properties = Struct()

        core = properties.core = Struct()
        core.product_name = os.path.splitext(os.path.basename(inpath))[0]
        core.creation_date = datetime.strptime(name_attrs['creation_date'], "%Y%m%dT%H%M%S")
        core.validity_start = datetime.strptime(name_attrs['validity_start'], "%Y%m%dT%H%M%S")
        core.validity_stop = datetime.strptime(name_attrs['validity_stop'], "%Y%m%dT%H%M%S")
        if not filename_only:
            core.footprint = get_footprint(inpath)

        s5p = properties.s5p = Struct()
        s5p.file_class = name_attrs['file_class']
        s5p.file_type = name_attrs['file_type']
        s5p.orbit = int(name_attrs['orbit'])
        s5p.collection = int(name_attrs['collection'])
        s5p.processor_version = int(name_attrs['processor_version'])

        return properties


class Sentinel5PAuxiliaryProduct(Sentinel5PProduct):

    def __init__(self, product_type, extension="nc"):
        super(Sentinel5PAuxiliaryProduct, self).__init__(product_type)
        pattern = [
            r"S5P",
            r"(?P<file_class>.{4})",
            r"(?P<file_type>%s)" % product_type[4:],
            r"(?P<validity_start>[\dT]{15})",
            r"(?P<validity_stop>[\dT]{15})",
            r"(?P<creation_date>[\dT]{15})"
        ]
        if extension:
            self.filename_pattern = "_".join(pattern) + r"\." + extension + "$"
        else:
            self.filename_pattern = "_".join(pattern) + "$"

    def archive_path(self, properties):
        validity_start = properties.core.validity_start
        if properties.core.validity_start == datetime.min:
            return os.path.join("sentinel-5p", self.product_type[4:])
        return os.path.join(
            "sentinel-5p",
            self.product_type[4:],
            validity_start.strftime("%Y"),
            validity_start.strftime("%m")
        )

    def analyze(self, paths, filename_only=False):
        inpath = paths[0]
        name_attrs = self.parse_filename(inpath)

        properties = Struct()

        core = properties.core = Struct()
        core.product_name = os.path.splitext(os.path.basename(inpath))[0]
        core.creation_date = datetime.strptime(name_attrs['creation_date'], "%Y%m%dT%H%M%S")
        if name_attrs['validity_start'] == "00000000T000000":
            core.validity_start = datetime.min
        else:
            core.validity_start = datetime.strptime(name_attrs['validity_start'], "%Y%m%dT%H%M%S")
        if name_attrs['validity_stop'] == "99999999T999999":
            core.validity_stop = datetime.max
        else:
            core.validity_stop = datetime.strptime(name_attrs['validity_stop'], "%Y%m%dT%H%M%S")

        s5p = properties.s5p = Struct()
        s5p.file_class = name_attrs['file_class']
        s5p.file_type = name_attrs['file_type']

        return properties


class Sentinel5PAuxiliaryNISEProduct(Sentinel5PAuxiliaryProduct):

    def __init__(self, product_type):
        super(Sentinel5PAuxiliaryNISEProduct, self).__init__(product_type)
        pattern = [
            r"NISE",
            r"SSMISF18",
            r"(?P<validity_start>[\d]{8})",
        ]
        self.filename_pattern = "_".join(pattern) + r"\.HDFEOS$"

    def analyze(self, paths, filename_only=False):
        inpath = paths[0]
        name_attrs = self.parse_filename(inpath)

        properties = Struct()

        core = properties.core = Struct()
        core.product_name = os.path.splitext(os.path.basename(inpath))[0]
        core.validity_start = datetime.strptime(name_attrs['validity_start'], "%Y%m%d")
        core.validity_stop = core.validity_start + timedelta(days=1)
        core.creation_date = core.validity_start

        s5p = properties.s5p = Struct()
        s5p.file_class = "OPER"
        s5p.file_type = "AUX_NISE__"

        return properties


def product_types():
    return MUNINN_PRODUCT_TYPES


def product_type_plugin(muninn_product_type):
    product_type = muninn_product_type[4:]
    if product_type in L1_PRODUCT_TYPES + L2_PRODUCT_TYPES:
        return Sentinel5PProduct(muninn_product_type)
    if product_type == "AUX_NISE__":
        return Sentinel5PAuxiliaryNISEProduct(muninn_product_type)
    if product_type in AUX_PRODUCT_TYPES:
        if product_type.startswith("CFG"):
            return Sentinel5PAuxiliaryProduct(muninn_product_type, "cfg")
        return Sentinel5PAuxiliaryProduct(muninn_product_type)
