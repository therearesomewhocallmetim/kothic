from __future__ import print_function
import re
import logging
import logging_config #to configure logging, no calls needed
from CssTree.CssElement import CssElement
from collections import namedtuple
from Util import StringWithSource


Block = namedtuple("Block", "name attrs")


MIN_ZOOM = 1
MAX_ZOOM = 19


BLOCK_SPLITTER = re.compile(r'([^@{]*)\s*\{(.*?)\}', re.DOTALL | re.MULTILINE)
ZOOM = re.compile(r'(.*?)(\|z[\d\-]*?)?(\[.*)?') #deprecated
ONE_ZOOM = re.compile(r'(\d{1,2})$')
ZOOM_RANGE = re.compile(r'(\d{1,2})-(\d{1,2})$')
ZOOM_TO_MAX = re.compile(r'(\d{1,2})-$')


TAG_RE = re.compile(r'(^.*?)[\|\[$:]', re.MULTILINE)
ZOOM_RE = re.compile(r'.*?\|z([\d\-]*?)[\[$:]')
SELECTORS_RE = re.compile(r'(\[.*?\])')
SUB_RE = re.compile(r'.*:(.*)$')
ONE_SELECTOR_RE = re.compile(r'\[(.*?)\]')


class BlockSplitter:
    """
    Should also be initializeable by a preprocessed file
    """
    def __init__(self, preprocessed_blocks, write_to_file=False):
        self.blocks = preprocessed_blocks
        self.write_to_file = write_to_file
        self.blocks_by_zoom_level = dict(map(lambda i: (i, {}), range(MIN_ZOOM, MAX_ZOOM +1)))


    def process(self):
        self.split_commas()
        self.process_blocks_by_zoom_level()

        if self.write_to_file:
            self.write()


    def process_blocks_by_zoom_level(self):
        for zoom in self.blocks_by_zoom_level:
            self.process_zoom_level(zoom, self.blocks_by_zoom_level[zoom])


    def process_zoom_level(self, zoom, block):
        clean_block = {}
        block_keys = sorted(block.keys())
        old_block = Block("", [])
        for tag in block_keys:
            attrs = block[tag]
            if tag == old_block.name:
                old_block.attrs.extend(attrs)
            else:
                if old_block.name:
                    clean_block[old_block.name] = self.parse_attributes(old_block.attrs, tag, zoom)
                old_block = Block(tag, attrs)
        self.blocks_by_zoom_level[zoom] = clean_block


    def parse_attributes(self, list_of_attrs, tag, zoom):
        ret = {} #attribute : StringWithSource(value, imported_from)
        for attr, source in list_of_attrs.iteritems():
            key, val = map(str.strip, attr.split(":", 1))
            if key in ret:
                logging.warning("Duplicate value for attribute {} ({}) for tag {} on zoom {}. First declared in {}".format(key, val, tag, zoom, ret[key].source))

            ret[key] = StringWithSource(val, source)
        return ret


    def clean_split_by(self, string, separator):
        return filter(lambda x: x != "", map(lambda x: x.strip(), string.split(separator)))


    def all_zooms_in_css_range(self, str_range):
        min_zoom = -1
        max_zoom = -1

        if not str_range:
            min_zoom = MIN_ZOOM
            max_zoom = MAX_ZOOM

        elif ONE_ZOOM.match(str_range):
            min_zoom = int(str_range)
            max_zoom = min_zoom

        elif ZOOM_TO_MAX.match(str_range):
            min_zoom = int(str_range[:-1])
            max_zoom = MAX_ZOOM

        elif ZOOM_RANGE.match(str_range):
            found = ZOOM_RANGE.findall(str_range)[0]
            (min_zoom, max_zoom) = map(lambda x: int(x), found)

        if max_zoom < 0 or min_zoom < 0 or max_zoom < min_zoom:
            raise Exception("Failed to parse the zoom levels")

        max_zoom = MAX_ZOOM if max_zoom > MAX_ZOOM else max_zoom
        min_zoom = MIN_ZOOM if min_zoom < MIN_ZOOM else min_zoom

        return range(min_zoom, max_zoom + 1)


    def split_keys_by_zoom(self, keys):
        ret = []
        for key in keys:
            parts_list = ZOOM.findall(key)
            if not parts_list:
                logging.error("Unparseable key {}".format(key))
                continue
            parts = parts_list[0]
            if parts:
                selector, zoom = parts[0], parts[1][2:]
                print(">>>> {} : {}".format(selector, zoom))
                all_zooms = self.all_zooms_in_css_range(zoom)
                ret.append(map(lambda x: (selector, x), all_zooms))
            else:
                logging.error("Got an unparseable node and zoom level: {}".format(key))
                logging.warning("NOTE THAT THIS TAG HAS BEEN IGNORED AND MUST BE PROCESSED IN THE FUTURE!")
        return ret


    def clean_up_attribute_block(self, attributes, key, imported_from):
        last_attr = ""
        clean_attributes = []
        for a in attributes:
            if a == last_attr:
                logging.warning("Duplicate attribute {} for tag/zoom {} imported from  {}".format(a, key, imported_from))
                continue
            clean_attributes.append(a)
        return clean_attributes


    def filter_attributes_against_processed(self, clean_attributes, element, imported_from):
        filtered_attributes = []
        for a in clean_attributes:
            if a in self.blocks_by_zoom_level[element.zoom][element]:
                logging.warning("Duplicate attribute {} for tag {} imported from {}".format(a, element, imported_from))
            else:
                filtered_attributes.append(a)
        return filtered_attributes


    def split_commas(self):
        for block, imported_from in self.blocks:
            found = BLOCK_SPLITTER.findall(block)
            for entry in found:
                keys = self.clean_split_by(entry[0], ",")
                attributes = sorted(self.clean_split_by(entry[1], ";")) #TODO attributes should also be a dictionary. Or should they?

                clean_attributes = self.clean_up_attribute_block(attributes, entry[0], imported_from)

                for key in keys:
                    elements = self.css_key_factory(key)
                    self.add_elements_to_zoom_level(elements, clean_attributes, imported_from)


    def add_elements_to_zoom_level(self, elements, clean_attributes, imported_from):
        for element in elements:
            if element in self.blocks_by_zoom_level[element.zoom]:
                filtered_attributes = self.filter_attributes_against_processed(clean_attributes, element, imported_from)
                self.blocks_by_zoom_level[element.zoom][element].update(self.map_attrs_to_import_source(filtered_attributes, imported_from))
            else:
                self.blocks_by_zoom_level[element.zoom][element] = self.map_attrs_to_import_source(clean_attributes, imported_from)


    def map_attrs_to_import_source(self, attributes, imported_from):
        return dict(map(lambda x: (x, imported_from), attributes))


    def write(self):
        print("Writing split blocks by zoom, num blocks {}".format(len(self.blocks_by_zoom_level)))
        with open("../../out/split_by_commas.mapcss", "w") as out_file:
            for zoom in sorted(self.blocks_by_zoom_level.keys()):
                blocks = self.blocks_by_zoom_level[zoom]
            # for zoom, blocks in self.blocks_by_zoom_level:
                out_file.write("   /* ===== ZOOM {} ===== */\n\n".format(zoom))
                keys = blocks.keys()
                keys.sort(key=lambda x : x.tag)
                for tag in keys:
                    attrs = blocks[tag]
                    out_file.write("{} {{\n".format(tag))
                    for attr in attrs:
                        out_file.write("    {}: {}; /* == {} == */\n".format(attr, attrs[attr].string, attrs[attr].source))
                    out_file.write("}\n\n")


    def css_key_factory(self, str_key):
        # type: (str) -> [CssElement]
        tag_list = TAG_RE.findall(str_key)
        tag = tag_list[0] if tag_list else str_key

        zoom_list = ZOOM_RE.findall(str_key)
        zoom = zoom_list[0] if zoom_list else ""

        selectors_list = SELECTORS_RE.findall(str_key)

        str_key = TAG_RE.sub("", str_key)
        str_key = ZOOM_RE.sub("", str_key)
        str_key = SELECTORS_RE.sub("", str_key)

        subclass_list = SUB_RE.findall(str_key)
        subclass = subclass_list[0] if subclass_list else ""
        all_zooms = self.all_zooms_in_css_range(zoom)
        ret = map(lambda z: CssElement(tag, z, selectors_list, subclass), all_zooms)
        return ret



if __name__ == "__main__":


    blockSplitter = BlockSplitter([])
    # print(blockSplitter.all_zooms_in_css_range("10"))
    # print(blockSplitter.all_zooms_in_css_range("10-"))
    # print(blockSplitter.all_zooms_in_css_range("10-12"))
    # print(blockSplitter.all_zooms_in_css_range("10-25"))

    # print(blockSplitter.split_key_by_components("*::*"))
    # print(blockSplitter.split_key_by_components("*"))
    # print(blockSplitter.split_key_by_components("*|z12"))
    # print(blockSplitter.split_key_by_components("*::int_name "))
    # print(blockSplitter.split_key_by_components("line|z5[highway=world_level]"))
    # print(blockSplitter.css_key_factory("line|z17-18[highway=footway][tunnel?]::tunnelBackground"))

    pass

