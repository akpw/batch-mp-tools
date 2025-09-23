# coding=utf8
## Copyright (c) 2014 Arseniy Kuznetsov
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.

import os
import pygtrie
from collections import namedtuple
from batchmp.fstools.walker import DWalker
from batchmp.fstools.builders.fsentry import FSEntryType
from batchmp.fstools.fsutils import FSH
from batchmp.fstools.builders.fsprms import FSEntryParamsOrganize
from batchmp.fstools.builders.fsb import FSEntryBuilderOrganize


class VirtualOrganizer:
    """ Helper class for creating virtual organized views without moving files.
    """
    
    def __init__(self, fs_entry_params):
        self.fs_entry_params = fs_entry_params
        self.dir_trie = pygtrie.StringTrie(separator=os.path.sep)
        self.dir_sizes = {}
        
    def build_virtual_structure(self):
        """ Build the virtual directory structure from FSEntry data.
        """
        entries_to_process = list(DWalker.entries(self.fs_entry_params))
        fcnt = 0
        
        for entry in entries_to_process:
            if entry.type == FSEntryType.FILE and hasattr(entry, 'target_path'):
                fcnt += 1
                target_dir = os.path.dirname(entry.target_path)
                if not self.dir_trie.has_key(target_dir):
                    self.dir_trie[target_dir] = []
                self.dir_trie[target_dir].append(entry)
        
        if fcnt == 0:
            return False
            
        self._calculate_directory_sizes()
        return True
    
    def max_directory_depth(self):
        """ Calculate required depth based on organization structure.
        """
        max_depth = 0
        for target_path in self.dir_trie.keys():
            rel_path = os.path.relpath(target_path, self.fs_entry_params.src_dir)
            if rel_path != '.':
                depth = len(rel_path.split(os.path.sep))
                max_depth = max(max_depth, depth)
        return max_depth        

    def organize_virtual_walker(self):
        """ Create walker for organize method with simple alphabetical sorting.
        """
        root_dir = self.fs_entry_params.src_dir
        
        def virtual_walker(root_dir):
            # Build hierarchical tree structure from trie
            tree = {}
            for target_path, files in self.dir_trie.items():
                rel_path = os.path.relpath(target_path, root_dir)
                if rel_path == '.': 
                    continue  # Skip files that stay in root
                
                # Build nested tree structure
                parts = rel_path.split(os.path.sep)
                node = tree
                for part in parts:
                    node = node.setdefault(part, {})
                node['__files__'] = [f.basename for f in files]
            
            # Recursive function to yield all levels of the tree
            def walk_tree(current_path, subtree):
                # Get directories and files at current level (sorted alphabetically)
                subdirs = sorted([k for k in subtree.keys() if k != '__files__'])
                files = sorted(subtree.get('__files__', []))
                
                # Yield current directory
                yield current_path, subdirs, files
                
                # Recursively yield subdirectories
                for subdir in subdirs:
                    subdir_path = os.path.join(current_path, subdir)
                    yield from walk_tree(subdir_path, subtree[subdir])
            
            # Start walking from root
            yield from walk_tree(root_dir, tree)
        
        return virtual_walker
    
    def organize_preview_params(self, max_depth):
        """ Create FSEntry parameters for organize preview with standard sorting.
        """
        preview_params = FSEntryParamsOrganize({
            'all_files': True,
            'all_dirs': True,
            'end_level': max_depth
        })
        preview_params.src_dir = self.fs_entry_params.src_dir
        # Override builder for preview
        preview_params.__dict__['fs_entry_builder'] = FSEntryBuilderOrganize()
        return preview_params        
    
    def print_virtual_walker(self):
        """ Create walker for print_organized_view with full sorting support.
        """
        root_dir = self.fs_entry_params.src_dir
        
        def virtual_walker(root_dir):
            # Build hierarchical tree structure from trie
            tree = {}
            for target_path, files in self.dir_trie.items():
                rel_path = os.path.relpath(target_path, root_dir)
                if rel_path == '.': 
                    # Files that stay in root
                    tree.setdefault('__files__', []).extend([f.basename for f in files])
                    continue
                
                # Build nested tree structure
                parts = rel_path.split(os.path.sep)
                node = tree
                for part in parts:
                    node = node.setdefault(part, {})
                node['__files__'] = [f.basename for f in files]
            
            # Recursive function to yield all levels of the tree
            def walk_tree(current_path, subtree):
                # Get directories and files at current level
                subdirs = [k for k in subtree.keys() if k != '__files__']
                files = subtree.get('__files__', [])
                
                # Apply custom sorting for size-based sorts (FSEntry can't handle virtual paths)
                if self.fs_entry_params.by_size:
                    subdirs = self._sort_entries_by_size(subdirs, is_dir=True)
                    files = self._sort_entries_by_size(files, is_dir=False)
                
                # Yield current directory (use copies to prevent DWalker from modifying our sorted lists)
                yield current_path, subdirs.copy(), files.copy()
                
                # Recursively yield subdirectories
                for subdir in subdirs:
                    subdir_path = os.path.join(current_path, subdir)
                    yield from walk_tree(subdir_path, subtree[subdir])
            
            # Start walking from root
            yield from walk_tree(root_dir, tree)
        
        return virtual_walker
    
    def print_formatter_with_sizes(self):
        """ Create formatter for print_organized_view that shows sizes for both files and virtual dirs.
        """
        def size_aware_formatter(entry):
            if self.fs_entry_params.show_size:
                if entry.type == FSEntryType.FILE:
                    # For files, show size from their real path (original file location)
                    # Find the original file in our file mapping
                    original_file = None
                    for target_path, files in self.dir_trie.items():
                        for file_entry in files:
                            if file_entry.basename == entry.basename:
                                original_file = file_entry
                                break
                        if original_file:
                            break
                    
                    if original_file:
                        try:
                            fsize = os.path.getsize(original_file.realpath)
                            size_str = FSH.fs_size(fsize)
                            return f" {size_str} {entry.basename}"
                        except (OSError, IOError):
                            pass
                            
                elif entry.type == FSEntryType.DIR:
                    # For virtual directories, show aggregated size of contained files
                    # Find the corresponding target path for this virtual directory
                    virtual_path = entry.realpath
                    if virtual_path in self.dir_sizes:
                        total_size = self.dir_sizes[virtual_path]
                        if total_size > 0:
                            size_str = FSH.fs_size(total_size)
                            return f" {size_str} {entry.basename}"
            
            # For directories without size info or when size not requested, just return basename
            return entry.basename
        
        return size_aware_formatter
    
    def print_preview_params(self, max_depth):
        """ Create FSEntry parameters for print_organized_view with advanced sorting.
        """
        
        # For size-based sorting, we need to completely bypass FSEntry sorting
        # since it tries to access virtual file paths that don't exist
        if self.fs_entry_params.by_size:
            # Create a custom FSEntry class that bypasses sorting
            class NoSortFSEntryParamsOrganize(FSEntryParamsOrganize):
                class NoSortFilesDescriptor:
                    def __set__(self, instance, value):
                        # Just store the files without any sorting or filtering
                        # The virtual walker already sorted them correctly
                        instance._fnames = value
                    def __get__(self, instance, owner):
                        return getattr(instance, '_fnames', [])
                
                class NoSortDirsDescriptor:
                    def __set__(self, instance, value):
                        # Just store the dirs without any sorting or filtering
                        # The virtual walker already sorted them correctly
                        DNames = namedtuple('DNames', ['passed', 'enclosing'])
                        instance._dnames = DNames(value, [])
                    def __get__(self, instance, owner):
                        DNames = namedtuple('DNames', ['passed', 'enclosing'])
                        return getattr(instance, '_dnames', DNames([], []))
                
                # Override the descriptors to bypass sorting
                fnames = NoSortFilesDescriptor()
                dnames = NoSortDirsDescriptor()
            
            preview_params = NoSortFSEntryParamsOrganize({
                'all_files': True,
                'all_dirs': True,
                'end_level': max_depth,
                'show_size': False  # We handle sizes with custom formatter
            })
            preview_params.src_dir = self.fs_entry_params.src_dir
            preview_params.sort = 'na'  # Won't be used due to custom descriptors
        else:
            # For name-based sorting, let FSEntry handle it normally
            preview_params = FSEntryParamsOrganize({
                'all_files': True,
                'all_dirs': True,
                'end_level': max_depth,
                'show_size': False  # We handle sizes with custom formatter
            })
            preview_params.src_dir = self.fs_entry_params.src_dir
            preview_params.sort = self.fs_entry_params.sort
        
        # Override builder for preview
        preview_params.__dict__['fs_entry_builder'] = FSEntryBuilderOrganize()
        return preview_params


    ## Helpers
    def _calculate_directory_sizes(self):
        """ Pre-calculate directory sizes by aggregating file sizes.
        """
        if self.fs_entry_params.show_size:
            for target_path, files in self.dir_trie.items():
                total_size = 0
                for file_entry in files:
                    try:
                        fsize = os.path.getsize(file_entry.realpath)
                        total_size += fsize
                    except (OSError, IOError):
                        pass
                self.dir_sizes[target_path] = total_size
    
    def _sort_entries_by_size(self, items, is_dir):
        """ Sort items by size when FSEntry sorting would fail due to virtual paths.
        """
        if not items:
            return items
            
        if is_dir:
            # For directories, use aggregated sizes from dir_sizes
            def size_key(dirname):
                # Find the virtual directory path that corresponds to this dirname
                for target_path in self.dir_sizes.keys():
                    if target_path.endswith(os.sep + dirname) or target_path.endswith(dirname):
                        return self.dir_sizes.get(target_path, 0)
                return 0
            sort_key = size_key
        else:
            # For files, look up original file size from dir_trie
            def file_size_key(filename):
                # Find the file entry in dir_trie to get its real path
                for target_path, files in self.dir_trie.items():
                    for file_entry in files:
                        if file_entry.basename == filename:
                            try:
                                return os.path.getsize(file_entry.realpath)
                            except (OSError, IOError):
                                return 0
                return 0
            sort_key = file_size_key
        
        return sorted(items, key=sort_key, reverse=self.fs_entry_params.descending)