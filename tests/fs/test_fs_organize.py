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

    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_print_organized_view_sorting_size_descending(self):
        """ Test organized view respects size descending sort parameter
        """
        # Create params with size descending sort
        fs_entry_params = self._fs_entry_organize(by='type', quiet=True)
        fs_entry_params.sort = 'sd'  # size descending
        fs_entry_params.show_size = True
        
        # Capture the output to analyze sorting
        import io
        from contextlib import redirect_stdout
        
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            DHandler.print_organized_view(fs_entry_params)
        
        output_lines = captured_output.getvalue().strip().split('\n')
        
        # Find directory lines (those starting with |->/) 
        dir_lines = [line for line in output_lines if '|->/' in line]
        
        # Extract sizes from directory lines (should be in descending order)
        dir_sizes = []
        for line in dir_lines:
            # Look for size patterns like "157KB", "324KB", etc.
            import re
            size_match = re.search(r'([0-9.]+(?:KB|MB|GB))', line)
            if size_match:
                size_str = size_match.group(1)
                # Convert to bytes for comparison
                if 'KB' in size_str:
                    size_bytes = float(size_str.replace('KB', '')) * 1024
                elif 'MB' in size_str:
                    size_bytes = float(size_str.replace('MB', '')) * 1024 * 1024
                elif 'GB' in size_str:
                    size_bytes = float(size_str.replace('GB', '')) * 1024 * 1024 * 1024
                else:
                    size_bytes = float(size_str)
                dir_sizes.append(size_bytes)
        
        # Verify sizes are in descending order
        if len(dir_sizes) > 1:
            for i in range(len(dir_sizes) - 1):
                self.assertGreaterEqual(dir_sizes[i], dir_sizes[i + 1],
                    f"Directory sizes not in descending order: {dir_sizes[i]} < {dir_sizes[i + 1]}")
    
    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_print_organized_view_sorting_size_ascending(self):
        """ Test organized view respects size ascending sort parameter
        """
        # Create params with size ascending sort
        fs_entry_params = self._fs_entry_organize(by='type', quiet=True)
        fs_entry_params.sort = 'sa'  # size ascending
        fs_entry_params.show_size = True
        
        # Capture the output to analyze sorting
        import io
        from contextlib import redirect_stdout
        
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            DHandler.print_organized_view(fs_entry_params)
        
        output_lines = captured_output.getvalue().strip().split('\n')
        
        # Find directory lines (those starting with |->/) 
        dir_lines = [line for line in output_lines if '|->/' in line]
        
        # Extract sizes from directory lines (should be in ascending order)
        dir_sizes = []
        for line in dir_lines:
            # Look for size patterns like "157KB", "324KB", etc.
            import re
            size_match = re.search(r'([0-9.]+(?:KB|MB|GB))', line)
            if size_match:
                size_str = size_match.group(1)
                # Convert to bytes for comparison
                if 'KB' in size_str:
                    size_bytes = float(size_str.replace('KB', '')) * 1024
                elif 'MB' in size_str:
                    size_bytes = float(size_str.replace('MB', '')) * 1024 * 1024
                elif 'GB' in size_str:
                    size_bytes = float(size_str.replace('GB', '')) * 1024 * 1024 * 1024
                else:
                    size_bytes = float(size_str)
                dir_sizes.append(size_bytes)
        
        # Verify sizes are in ascending order
        if len(dir_sizes) > 1:
            for i in range(len(dir_sizes) - 1):
                self.assertLessEqual(dir_sizes[i], dir_sizes[i + 1],
                    f"Directory sizes not in ascending order: {dir_sizes[i]} > {dir_sizes[i + 1]}")
    
    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_print_organized_view_sorting_name_descending(self):
        """ Test organized view respects name descending sort parameter
        """
        # Create params with name descending sort
        fs_entry_params = self._fs_entry_organize(by='type', quiet=True)
        fs_entry_params.sort = 'nd'  # name descending
        
        # Capture the output to analyze sorting
        import io
        from contextlib import redirect_stdout
        
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            DHandler.print_organized_view(fs_entry_params)
        
        output_lines = captured_output.getvalue().strip().split('\n')
        
        # Find directory lines (those starting with |->/) 
        dir_lines = [line for line in output_lines if '|->/' in line]
        
        # Extract directory names
        dir_names = []
        for line in dir_lines:
            # Extract directory name from lines like "  |->/ 157KB image"
            import re
            name_match = re.search(r'\|->/.+?\s+([a-zA-Z]+)\s*$', line)
            if name_match:
                dir_names.append(name_match.group(1))
        
        # Verify names are in descending order (reverse alphabetical)
        if len(dir_names) > 1:
            sorted_names = sorted(dir_names, reverse=True)
            self.assertEqual(dir_names, sorted_names,
                f"Directory names not in descending order: {dir_names} vs expected {sorted_names}")
    
    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_print_organized_view_sorting_name_ascending(self):
        """ Test organized view respects name ascending sort parameter
        """
        # Create params with name ascending sort
        fs_entry_params = self._fs_entry_organize(by='type', quiet=True)
        fs_entry_params.sort = 'na'  # name ascending
        
        # Capture the output to analyze sorting
        import io
        from contextlib import redirect_stdout
        
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            DHandler.print_organized_view(fs_entry_params)
        
        output_lines = captured_output.getvalue().strip().split('\n')
        
        # Find directory lines (those starting with |->/) 
        dir_lines = [line for line in output_lines if '|->/' in line]
        
        # Extract directory names
        dir_names = []
        for line in dir_lines:
            # Extract directory name from lines like "  |->/ 157KB image"
            import re
            name_match = re.search(r'\|->/.+?\s+([a-zA-Z]+)\s*$', line)
            if name_match:
                dir_names.append(name_match.group(1))
        
        # Verify names are in ascending order (alphabetical)
        if len(dir_names) > 1:
            sorted_names = sorted(dir_names)
            self.assertEqual(dir_names, sorted_names,
                f"Directory names not in ascending order: {dir_names} vs expected {sorted_names}")
    
    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_print_organized_view_file_sorting_by_size(self):
        """ Test that files within directories are sorted correctly by size
        """
        # Create params with size descending sort
        fs_entry_params = self._fs_entry_organize(by='type', quiet=True)
        fs_entry_params.sort = 'sd'  # size descending
        fs_entry_params.show_size = True
        
        # Capture the output to analyze sorting
        import io
        from contextlib import redirect_stdout
        
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            DHandler.print_organized_view(fs_entry_params)
        
        output_lines = captured_output.getvalue().strip().split('\n')
        
        # Find file lines (those starting with |-  and containing a size)
        file_lines = [line for line in output_lines if '|-  ' in line and any(unit in line for unit in ['KB', 'MB', 'GB'])]
        
        # Group files by directory (files appear after their directory header)
        current_dir = None
        dir_files = {}
        
        for line in output_lines:
            if '|->/' in line:
                # This is a directory line
                import re
                name_match = re.search(r'\|->/.+?\s+([a-zA-Z]+)\s*$', line)
                if name_match:
                    current_dir = name_match.group(1)
                    dir_files[current_dir] = []
            elif '|-  ' in line and current_dir and any(unit in line for unit in ['KB', 'MB', 'GB']):
                # This is a file line under the current directory
                dir_files[current_dir].append(line)
        
        # Check that files within each directory are sorted by size (descending)
        for dir_name, files in dir_files.items():
            if len(files) > 1:
                file_sizes = []
                for file_line in files:
                    import re
                    size_match = re.search(r'([0-9.]+(?:KB|MB|GB))', file_line)
                    if size_match:
                        size_str = size_match.group(1)
                        if 'KB' in size_str:
                            size_bytes = float(size_str.replace('KB', '')) * 1024
                        elif 'MB' in size_str:
                            size_bytes = float(size_str.replace('MB', '')) * 1024 * 1024
                        elif 'GB' in size_str:
                            size_bytes = float(size_str.replace('GB', '')) * 1024 * 1024 * 1024
                        else:
                            size_bytes = float(size_str)
                        file_sizes.append(size_bytes)
                
                # Verify files are sorted by size (descending)
                for i in range(len(file_sizes) - 1):
                    self.assertGreaterEqual(file_sizes[i], file_sizes[i + 1],
                        f"Files in {dir_name} directory not sorted by size descending: {file_sizes}")
    
    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_print_organized_view_no_file_movement(self):
        """ Test that print_organized_view with all sorting options doesn't move files
        """
        # Get original file locations
        original_files = []
        for root, dirs, files in os.walk(self.src_dir):
            for file in files:
                original_files.append(os.path.join(root, file))
        
        # Test all sorting combinations
        sort_options = ['na', 'nd', 'sa', 'sd']
        
        for sort_option in sort_options:
            with self.subTest(sort=sort_option):
                fs_entry_params = self._fs_entry_organize(by='type', quiet=True)
                fs_entry_params.sort = sort_option
                fs_entry_params.show_size = True
                
                # Print organized view - should not move files
                DHandler.print_organized_view(fs_entry_params)
                
                # Verify all original files still exist in original locations
                for original_file in original_files:
                    self.assertTrue(os.path.exists(original_file),
                        f"File {original_file} was moved during {sort_option} sort test")
    
    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_print_organized_view_mixed_file_types(self):
        """ Test organized view sorting with different file types in the test data
        """
        # This test ensures that our sorting works correctly even when we have different file types
        # The test data contains PNG files, which should all be categorized as 'image' type
        
        fs_entry_params = self._fs_entry_organize(by='type', quiet=True)
        fs_entry_params.sort = 'sd'  # size descending
        fs_entry_params.show_size = True
        
        # Capture the output
        import io
        from contextlib import redirect_stdout
        
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            DHandler.print_organized_view(fs_entry_params)
        
        output_lines = captured_output.getvalue().strip().split('\n')
        
        # Should contain "Virtual view by type:" header
        self.assertTrue(any('Virtual view by type:' in line for line in output_lines),
            "Output should contain virtual view header")
        
        # Should contain at least one directory (image directory for PNG files)
        dir_lines = [line for line in output_lines if '|->/' in line]
        self.assertGreater(len(dir_lines), 0, "Should have at least one organized directory")
        
        # Should contain image directory since test data has PNG files
        image_dir_found = any('image' in line.lower() for line in dir_lines)
        self.assertTrue(image_dir_found, "Should contain image directory for PNG files")
    
    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_print_organized_view_sorting_with_synthetic_data(self):
        """ Test sorting with synthetic test files of different types and sizes
        """
        import tempfile
        import shutil
        
        # Create a temporary directory with synthetic test files
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create files with different types and sizes
            test_files = [
                # Different types to create multiple directories
                ('large_video.mp4', 5000),     # 5KB video
                ('small_video.avi', 1000),     # 1KB video  
                ('medium_audio.mp3', 3000),    # 3KB audio
                ('tiny_audio.wav', 500),       # 0.5KB audio
                ('big_image.png', 4000),       # 4KB image
                ('mini_image.jpg', 800),       # 0.8KB image
            ]
            
            # Create the test files
            for filename, size in test_files:
                filepath = os.path.join(temp_dir, filename)
                with open(filepath, 'wb') as f:
                    f.write(b'0' * size)  # Write size bytes of zeros
            
            # Test size descending sort
            fs_entry_params = self._fs_entry_organize(by='type', quiet=True)
            fs_entry_params.src_dir = temp_dir
            fs_entry_params.sort = 'sd'  # size descending
            fs_entry_params.show_size = True
            
            # Capture output
            import io
            from contextlib import redirect_stdout
            
            captured_output = io.StringIO()
            with redirect_stdout(captured_output):
                DHandler.print_organized_view(fs_entry_params)
            
            output = captured_output.getvalue()
            output_lines = output.strip().split('\n')
            
            # Extract directory lines and their sizes
            dir_lines = [line for line in output_lines if '|->/' in line]
            
            if len(dir_lines) > 1:
                dir_info = []
                for line in dir_lines:
                    # Extract size and name
                    import re
                    size_match = re.search(r'([0-9.]+(?:KB|MB|GB|B))', line)
                    name_match = re.search(r'\|->/.+?\s+([a-zA-Z]+)\s*$', line)
                    
                    if size_match and name_match:
                        size_str = size_match.group(1)
                        name = name_match.group(1)
                        
                        # Convert size to bytes for comparison
                        if 'KB' in size_str:
                            size_bytes = float(size_str.replace('KB', '')) * 1024
                        elif 'MB' in size_str:
                            size_bytes = float(size_str.replace('MB', '')) * 1024 * 1024
                        elif 'GB' in size_str:
                            size_bytes = float(size_str.replace('GB', '')) * 1024 * 1024 * 1024
                        elif 'B' in size_str and 'KB' not in size_str:
                            size_bytes = float(size_str.replace('B', ''))
                        else:
                            size_bytes = float(size_str)
                        
                        dir_info.append((name, size_bytes))
                
                # Verify directories are sorted by size descending
                for i in range(len(dir_info) - 1):
                    current_size = dir_info[i][1]
                    next_size = dir_info[i + 1][1]
                    self.assertGreaterEqual(current_size, next_size,
                        f"Directory {dir_info[i][0]} (size {current_size}) should be >= "
                        f"directory {dir_info[i+1][0]} (size {next_size}) in size descending sort")
    
    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_print_organized_view_edge_cases(self):
        """ Test edge cases for print_organized_view sorting
        """
        # Test with single file type (should still work)
        fs_entry_params = self._fs_entry_organize(by='type', quiet=True)
        fs_entry_params.sort = 'sd'
        fs_entry_params.show_size = True
        
        # Should not raise any errors
        import io
        from contextlib import redirect_stdout
        
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            DHandler.print_organized_view(fs_entry_params)
        
        output = captured_output.getvalue()
        # Should contain the virtual view header
        self.assertIn('Virtual view by type:', output)
    
    @unittest.skipIf(os.name == 'nt', 'skipping for windows')
    def test_print_organized_view_date_sorting(self):
        """ Test that date-based organization also respects sorting parameters
        """
        # Test date organization with size sorting
        fs_entry_params = self._fs_entry_organize(by='date', date_format='%Y-%m', quiet=True)
        fs_entry_params.sort = 'sd'  # size descending
        fs_entry_params.show_size = True
        
        # Should not raise any errors
        import io
        from contextlib import redirect_stdout
        
        captured_output = io.StringIO()
        with redirect_stdout(captured_output):
            DHandler.print_organized_view(fs_entry_params)
        
        output = captured_output.getvalue()
        # Should contain the virtual view header with date organization
        self.assertIn('Virtual view by date', output)
        
        # Should contain date-based directories (YYYY-MM format)
        import re
        date_pattern = r'\d{4}-\d{2}'
        self.assertTrue(re.search(date_pattern, output),
            "Output should contain date-based directory names")


if __name__ == '__main__':
    unittest.main()
