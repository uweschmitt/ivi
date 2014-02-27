
from collections import defaultdict
import glob
import os

def collect_files(root, postfixes=(".mzXML", ".pep.xml"), verbose=True):
    collected = defaultdict(list)
    for subdir_name in os.listdir(root):
        subdir_path = os.path.join(root, subdir_name)
        if os.path.isdir(subdir_path):
            if verbose:
                print "scan files in ", subdir_name
            for file_name in os.listdir(subdir_path):
                for postfix in postfixes:
                    if file_name.endswith(postfix):
                        if verbose:
                            print "  collect", file_name
                        full_path = os.path.join(subdir_path, file_name)
                        collected[postfix].append(full_path)
    return collected
