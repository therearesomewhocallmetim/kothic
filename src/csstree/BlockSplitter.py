from __future__ import print_function
import re
import logging
import logging_config #to configure logging, no calls needed
from CssTree.CssElement import CssElement



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
        print("Num of input blocks is: {}".format(len(preprocessed_blocks)))
        self.blocks = preprocessed_blocks
        self.split_blocks = {} # selector : list of attributes
        self.write_to_file = write_to_file
        self.blocks_by_zoom_level = self.init_blocks_by_zoom_level()
        print("Will write to file! {}".format(self.write_to_file))


    def init_blocks_by_zoom_level(self):
        ret = {}
        for i in range(MIN_ZOOM, MAX_ZOOM + 1):
            ret[i] = {} #tag with selectors and subclasses to attributes, selectors must be sorted
        return ret


    def process(self):
        self.split_commas()
        self.process_blocks_by_zoom_level()

        if self.write_to_file:
            self.write()
            pass

    def process_blocks_by_zoom_level(self):
        for zoom in self.blocks_by_zoom_level:
            self.process_zoom_level(zoom, self.blocks_by_zoom_level[zoom])

    def process_zoom_level(self, zoom, block):
        clean_block = [] # another list of tuples
        block_keys = sorted(block.keys())
        # block.sort(key=lambda x: x[1]) #sort the tuples by the 0th element
        old_block = ("", [])
        for tag in block_keys:
            attrs = block[tag]
            if tag == old_block[0] :
                old_block[1].extend(attrs)
            else:
                if old_block[0]:
                    clean_block.append(old_block)
                old_block = (tag, attrs)
        self.blocks_by_zoom_level[zoom] = clean_block


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

        ret = [i for i in range(min_zoom, max_zoom + 1)]

        return ret




    def split_keys_by_zoom(self, keys):
        ret = []
        for key in keys:
            parts_list = ZOOM.findall(key)
            if not parts_list:
                print("Unparseable key {}".format(key))
                continue
            parts = parts_list[0]
            if parts:
                selector, zoom = parts[0], (parts[1] if not parts else parts[1][2:])
                print(">>>> {} : {}".format(selector, zoom))
                all_zooms = self.all_zooms_in_css_range(zoom)
                ret.append(map(lambda x: (selector, x), all_zooms))
            else:
                print("Got an unparseable node and zoom level: {}".format(key))
                logging.warning("NOTE THAT THIS TAG HAS BEEN IGNORED AND MUST BE PROCESSED IN THE FUTURE!")
        return ret


    def split_commas(self):
        for block in self.blocks:
            found = BLOCK_SPLITTER.findall(block)
            for entry in found:
                keys = self.clean_split_by(entry[0], ",")
                attributes = self.clean_split_by(entry[1], ";")

                for key in keys:
                    elements = self.css_key_factory(key)
                    attrs = []
                    for element in elements:
                        attrs.extend(attributes)
                        # subclass = "{}"
                        subclass = "::{}".format(element.subclass) if element.subclass else ""
                        resulting_tag = "{}{}{}".format(element.tag, sorted(element.selectors), subclass)
                        # print("{} -> {}".format(resulting_tag, attrs))
                        if resulting_tag in self.blocks_by_zoom_level[element.zoom]:

                            # to remove soon
                            for a in attributes:
                                if a in self.blocks_by_zoom_level[element.zoom][resulting_tag]:
                                    print("Duplicate attribute {} for tag {} on zoom {}".format(a, resulting_tag, element.zoom))

                            self.blocks_by_zoom_level[element.zoom][resulting_tag].extend(attributes)
                        else:
                            self.blocks_by_zoom_level[element.zoom][resulting_tag] = attributes


    def old_write(self):
        print("Writing split blocks, num blocks {}".format(len(self.split_blocks)))
        with open("../../out/split_by_commas.mapcss", "w") as out_file:
            for block in self.split_blocks:
                out_file.write("{} {{\n".format(block))
                for attr in self.split_blocks[block]:
                    out_file.write("    {};\n".format(attr))
                out_file.write("}\n\n")


    def write(self):
        print("Writing split blocks by zoom, num blocks {}".format(len(self.blocks_by_zoom_level)))
        with open("../../out/split_by_commas.mapcss", "w") as out_file:
            for zoom in sorted(self.blocks_by_zoom_level.keys()):
                blocks = self.blocks_by_zoom_level[zoom]
            # for zoom, blocks in self.blocks_by_zoom_level:
                out_file.write("   /* ===== ZOOM {} ===== */\n\n".format(zoom))

                for tag, attrs in blocks:
                    out_file.write("{} {{\n".format(tag))
                    for attr in attrs:
                        out_file.write("    {};\n".format(attr))
                    # out_file.write(attrs)
                    out_file.write("}\n\n")


    def css_key_factory(self, str_key):
        # type: (str) -> [CssElement]
        tag_list = TAG_RE.findall(str_key)
        tag = tag_list[0] if tag_list else str_key

        zoom_list = ZOOM_RE.findall(str_key)
        zoom = zoom_list[0] if zoom_list else ""

        # if "][" in str_key:
        #     print("Str key contains ][")

        selectors_list = SELECTORS_RE.findall(str_key)
        # selectors = selectors_list[0] if selectors_list else ""

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



