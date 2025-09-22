#!/usr/bin/env python
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

import os, sys, unittest, datetime
from batchmp.fstools.dirtools import DHandler
from batchmp.fstools.builders.fsprms import FSEntryParamsBase, FSEntryParamsOrganize
from batchmp.fstools.builders.fsentry import FSEntryDefaults
from .test_fs_base import FSTest


class FSOrganizeTests(FSTest):
    def setUp(self):
        self.resetDataFromBackup(quiet=True)

    def tearDown(self):
        self.resetDataFromBackup(quiet=True)

    def _fs_entry_organize(self, by='type', date_format='%Y-%m-%d', target_dir=None, 
                          include=FSEntryDefaults.DEFAULT_INCLUDE, 
                          exclude=FSEntryDefaults.DEFAULT_EXCLUDE,
                          end_level=sys.maxsize, quiet=True):
        """Helper to create FSEntryParamsOrganize"""
        args = {
            'dir': self.src_dir,
            'by': by,
            'date_format': date_format,
            'target_dir': target_dir,
            'include': include,
            'exclude': exclude,
            'end_level': end_level,
            'all_dirs': True,
            'all_files': True,
            'quiet': quiet,
            'show_size': False
        }
        return FSEntryParamsOrganize(args)

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_organize_by_type(self):
        """ Test basic organization by type
        """
        fs_entry_params = self._fs_entry_organize(by='type')
        
        # Count original files
        fs_base_params = FSEntryParamsBase({'dir': self.src_dir})
        fcnt_orig, _, _ = DHandler.dir_stats(fs_base_params)
        
        # Organize files
        DHandler.organize(fs_entry_params)
        
        # Verify organized structure exists - all test files are PNG images
        organized_dir = os.path.join(self.src_dir, 'image')
        self.assertTrue(os.path.exists(organized_dir), 
                      "Expected image directory was not created")
        
        # Verify files were moved to organized directory
        files_in_organized = os.listdir(organized_dir)
        self.assertTrue(len(files_in_organized) > 0, 
                      "No files found in organized image directory")
    
    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_organize_by_date(self):
        """ Test basic organization by date
        """
        # Get actual modification date of first file to determine expected directory
        first_file = None
        for root, dirs, files in os.walk(self.src_dir):
            if files:
                first_file = os.path.join(root, files[0])
                break
        
        self.assertIsNotNone(first_file, "No files found in test data")
        
        file_mtime = os.path.getmtime(first_file)
        expected_date = datetime.datetime.fromtimestamp(file_mtime).strftime('%Y-%m-%d')
        
        fs_entry_params = self._fs_entry_organize(by='date')
        
        # Organize files
        DHandler.organize(fs_entry_params)
        
        # Verify organized structure exists
        organized_dir = os.path.join(self.src_dir, expected_date)
        self.assertTrue(os.path.exists(organized_dir), 
                      f"Expected date directory {expected_date} was not created")
        
        # Verify files were moved to organized directory
        files_in_organized = os.listdir(organized_dir)
        self.assertTrue(len(files_in_organized) > 0, 
                      f"No files found in organized date directory {expected_date}")

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_organize_by_type_with_target_dir(self):
        """ Test organization by type with custom target directory
        """
        target_dir = os.path.join(self.src_dir, 'organized_output')
        os.makedirs(target_dir, exist_ok=True)
        
        fs_entry_params = self._fs_entry_organize(by='type', target_dir=target_dir)
        
        # Organize files
        DHandler.organize(fs_entry_params)
        
        # Verify organized structure in target directory
        image_dir = os.path.join(target_dir, 'image')
        self.assertTrue(os.path.exists(image_dir), 
                      "Image directory was not created in target directory")
        
        files_in_image_dir = os.listdir(image_dir)
        self.assertTrue(len(files_in_image_dir) > 0, 
                      "No files found in organized image directory")

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_organize_by_date_default_format(self):
        """ Test organization by date with default YYYY-MM-DD format
        """
        fs_entry_params = self._fs_entry_organize(by='date', date_format='%Y-%m-%d')
        
        # Organize files
        DHandler.organize(fs_entry_params)
        
        # Check that date-based directories were created
        import re
        expected_pattern = r'\d{4}-\d{2}-\d{2}'
        created_dirs = [d for d in os.listdir(self.src_dir) 
                       if os.path.isdir(os.path.join(self.src_dir, d)) 
                       and re.match(expected_pattern, d)]
        
        self.assertTrue(len(created_dirs) > 0, 
                      f"No directories matching pattern {expected_pattern} were created")
    
    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_organize_by_date_hierarchical_format(self):
        """ Test organization by date with hierarchical Year/Month format
        """
        fs_entry_params = self._fs_entry_organize(by='date', date_format='%Y/%m')
        
        # Organize files
        DHandler.organize(fs_entry_params)
        
        # Check that year directory was created
        import re
        expected_pattern = r'\d{4}'
        created_dirs = [d for d in os.listdir(self.src_dir) 
                       if os.path.isdir(os.path.join(self.src_dir, d)) 
                       and re.match(expected_pattern, d)]
        
        self.assertTrue(len(created_dirs) > 0, 
                      f"No year directories matching pattern {expected_pattern} were created")
        
        # Check that month subdirectory exists
        year_dir = created_dirs[0]
        month_dirs = [d for d in os.listdir(os.path.join(self.src_dir, year_dir))
                     if os.path.isdir(os.path.join(self.src_dir, year_dir, d))
                     and re.match(r'\d{2}', d)]
        
        self.assertTrue(len(month_dirs) > 0, 
                      "No month subdirectories were created")
    
    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_organize_by_date_year_month_format(self):
        """ Test organization by date with Year-Month format
        """
        fs_entry_params = self._fs_entry_organize(by='date', date_format='%Y-%m')
        
        # Organize files
        DHandler.organize(fs_entry_params)
        
        # Check that date-based directories were created
        import re
        expected_pattern = r'\d{4}-\d{2}'
        created_dirs = [d for d in os.listdir(self.src_dir) 
                       if os.path.isdir(os.path.join(self.src_dir, d)) 
                       and re.match(expected_pattern, d)]
        
        self.assertTrue(len(created_dirs) > 0, 
                      f"No directories matching pattern {expected_pattern} were created")

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_organize_filtered_files(self):
        """ Test organization with file filtering
        """
        # Count files matching filter before organization
        fs_filter_params = FSEntryParamsBase({
            'dir': self.src_dir, 
            'include': '*test*',
            'all_dirs': True,
            'all_files': True,
            'end_level': 5  # Make sure we get all nested files
        })
        fcnt_filtered_before, _, _ = DHandler.dir_stats(fs_filter_params)
        
        fs_entry_params = self._fs_entry_organize(by='type', include='*test*')
        
        # Organize filtered files
        DHandler.organize(fs_entry_params)
        
        # Verify files were actually organized
        image_dir = os.path.join(self.src_dir, 'image')
        self.assertTrue(os.path.exists(image_dir), 
                      "Image directory was not created for filtered organization")
        
        # Count how many test files are now in organized directory
        organized_test_files = [f for f in os.listdir(image_dir) if 'test' in f.lower()]
        
        # Should have at least some test files organized
        self.assertTrue(len(organized_test_files) > 0, 
                      "No test files were organized despite matching filter")
        
        # Count remaining unfiltered files in original locations  
        fcnt_remaining, _, _ = DHandler.dir_stats(fs_filter_params)
        
        # Should have fewer matching files in original locations after organizing
        self.assertLessEqual(fcnt_remaining, fcnt_filtered_before,
                           "File count should decrease after organizing filtered files")

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_print_organized_view_by_type(self):
        """ Test organized view printing by type without moving files
        """
        fs_entry_params = self._fs_entry_organize(by='type', quiet=True)
        
        # Store original file count and locations
        fs_base_params = FSEntryParamsBase({'dir': self.src_dir})
        fcnt_orig, dcnt_orig, _ = DHandler.dir_stats(fs_base_params)
        
        # Get list of original files
        original_files = []
        for root, dirs, files in os.walk(self.src_dir):
            for file in files:
                original_files.append(os.path.join(root, file))
        
        # Print organized view (should not move files)
        DHandler.print_organized_view(fs_entry_params)
        
        # Verify files were NOT moved
        fcnt_after, dcnt_after, _ = DHandler.dir_stats(fs_base_params)
        self.assertEqual(fcnt_orig, fcnt_after, 
                        "File count changed - files were moved when they shouldn't have been")
        
        # Verify original files still exist in original locations
        for original_file in original_files:
            self.assertTrue(os.path.exists(original_file), 
                          f"Original file {original_file} no longer exists after print_organized_view")

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')  
    def test_print_organized_view_by_date(self):
        """ Test organized view printing by date without moving files
        """
        fs_entry_params = self._fs_entry_organize(by='date', date_format='%Y/%m', quiet=True)
        
        # Store original state
        fs_base_params = FSEntryParamsBase({'dir': self.src_dir})
        fcnt_orig, _, _ = DHandler.dir_stats(fs_base_params)
        
        # Print organized view (should not move files)
        DHandler.print_organized_view(fs_entry_params)
        
        # Verify files were NOT moved
        fcnt_after, _, _ = DHandler.dir_stats(fs_base_params)
        self.assertEqual(fcnt_orig, fcnt_after, 
                        "File count changed during organized view print")

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_print_organized_view_with_sizes(self):
        """ Test organized view printing with file sizes
        """
        fs_entry_params = self._fs_entry_organize(by='type', quiet=True)
        fs_entry_params.show_size = True
        
        # This should not raise any errors and should not move files
        original_files = []
        for root, dirs, files in os.walk(self.src_dir):
            for file in files:
                original_files.append(os.path.join(root, file))
        
        # Print organized view with sizes
        DHandler.print_organized_view(fs_entry_params)
        
        # Verify no files were moved
        for original_file in original_files:
            self.assertTrue(os.path.exists(original_file), 
                          f"File {original_file} was moved during size display test")

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_organize_recursive(self):
        """ Test organization with recursive file discovery
        """
        fs_entry_params = self._fs_entry_organize(by='type', end_level=5)
        
        # Count all files recursively
        fs_recursive_params = FSEntryParamsBase({
            'dir': self.src_dir,
            'end_level': 5,
            'all_dirs': True,
            'all_files': True
        })
        fcnt_orig, _, _ = DHandler.dir_stats(fs_recursive_params)
        
        # Organize files recursively
        DHandler.organize(fs_entry_params)
        
        # Verify organization happened (files should be moved to organized structure)
        image_dir = os.path.join(self.src_dir, 'image')
        self.assertTrue(os.path.exists(image_dir), 
                      "Recursive organization did not create image directory")
        
        # Count files in organized structure
        organized_files = []
        for root, dirs, files in os.walk(image_dir):
            organized_files.extend(files)
        
        # Should have organized the original files
        self.assertTrue(len(organized_files) > 0, 
                      "No files were organized recursively")

    def test_organize_empty_directory(self):
        """ Test organize behavior with empty directory
        """
        # Create empty subdirectory
        empty_dir = os.path.join(self.src_dir, 'empty_test')
        os.makedirs(empty_dir, exist_ok=True)
        
        fs_entry_params = self._fs_entry_organize(by='type', quiet=True)
        fs_entry_params.src_dir = empty_dir
        
        # This should not raise errors, just print "No files to organize view"
        DHandler.organize(fs_entry_params)
        
        # Should still be empty
        self.assertEqual(len(os.listdir(empty_dir)), 0, 
                        "Empty directory should remain empty")


if __name__ == '__main__':
    unittest.main()
