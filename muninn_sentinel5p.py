import os
import re
from datetime import datetime

from muninn.struct import Struct
from muninn.schema import Mapping, Text, Integer
from muninn.geometry import Point, LinearRing, Polygon


# Namespaces

class Sentinel5PNamespace(Mapping):
    file_class = Text(index=True)
    file_type = Text(index=True)
    orbit = Integer(index=True)
    collection = Integer(index=True)
    processor_version = Integer(index=True)


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

FILE_CLASSES = [
    'NRTI',  # near-real time processing
    'OFFL',  # offline processing
    'RPRO',  # reprocessing
    'TEST',  # test
]

PRODUCT_TYPES = []

for _type in L1_PRODUCT_TYPES:
    for _fileclass in FILE_CLASSES:
        PRODUCT_TYPES.append('S5P_%s_%s' % (_type, _fileclass))


for _type in L2_PRODUCT_TYPES:
    for _fileclass in FILE_CLASSES:
        if _fileclass == 'NRTI' and _type == 'L2__CH4':
            # There are no NRTI products for L2 CH4
            continue
        PRODUCT_TYPES.append("S5P_%s_%s" % (_type, _fileclass))


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
        self.use_enclosing_directory = False
        self.use_hash = False
        self.product_type = product_type
        # see https://earth.esa.int/web/sentinel/user-guides/sentinel-5p-tropomi/naming-convention
        pattern = [
            r"S5P",
            r"(?P<file_class>%s)" % product_type[-4:],  # e.g. "S5P_L2__NO2____NRTI" -> "NRTI"
            r"(?P<file_type>%s)" % product_type[4:-5],  # e.g. "S5P_L2__NO2____NRTI" -> "L2__NO2___"
            r"(?P<validity_start>[\dT]{15})",
            r"(?P<validity_stop>[\dT]{15})",
            r"(?P<orbit>.{5})",
            r"(?P<collection>.{2})",
            r"(?P<processor_version>.{6})",
            r"(?P<creation_date>[\dT]{15})"
        ]
        self.filename_pattern = "_".join(pattern) + r"\.nc$"

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

    def analyze(self, paths):
        inpath = paths[0]
        name_attrs = self.parse_filename(inpath)

        properties = Struct()

        core = properties.core = Struct()
        core.product_name = os.path.splitext(os.path.basename(inpath))[0]
        core.creation_date = datetime.strptime(name_attrs['creation_date'], "%Y%m%dT%H%M%S")
        core.validity_start = datetime.strptime(name_attrs['validity_start'], "%Y%m%dT%H%M%S")
        core.validity_stop = datetime.strptime(name_attrs['validity_stop'], "%Y%m%dT%H%M%S")
        core.footprint = get_footprint(inpath)

        s5p = properties.s5p = Struct()
        s5p.file_class = name_attrs['file_class']
        s5p.file_type = name_attrs['file_type']
        s5p.orbit = int(name_attrs['orbit'])
        s5p.collection = int(name_attrs['collection'])
        s5p.processor_version = int(name_attrs['processor_version'])

        return properties


def product_types():
    return PRODUCT_TYPES


def product_type_plugin(product_type):
    if product_type in PRODUCT_TYPES:
        return Sentinel5PProduct(product_type)
