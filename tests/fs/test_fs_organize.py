import os
import shutil
import unittest
from batchmp.cli.renamer.renamer_dispatch import RenameDispatcher

class TestOrganize(unittest.TestCase):
    def setUp(self):
        self.test_dir = os.path.join(os.path.dirname(__file__), 'test_organize_temp')
        os.makedirs(self.test_dir, exist_ok=True)
        # Create some test files
        with open(os.path.join(self.test_dir, 'test.txt'), 'w') as f:
            f.write('test')
        with open(os.path.join(self.test_dir, 'test.mp3'), 'w') as f:
            f.write('test')
        with open(os.path.join(self.test_dir, 'test.avi'), 'w') as f:
            f.write('test')
        with open(os.path.join(self.test_dir, 'test.jpg'), 'w') as f:
            f.write('test')

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def _run_organize(self, args):
        # This is a simplified way to run the command.
        # In a real scenario, you might need to mock sys.argv or use a different approach.
        arg_dict = {
            'sub_cmd': 'organize',
            'dir': self.test_dir,
            'quiet': True,
            'all_files': True, # include hidden files if any
            'include': '*'
        }
        arg_dict.update(args)
        
        # The dispatcher expects a dictionary of arguments
        dispatcher = RenameDispatcher()
        # The option_parser is what holds the arguments after parsing
        dispatcher.option_parser.parse_options = lambda: arg_dict
        dispatcher.dispatch()

    def test_organize_by_type(self):
        self._run_organize({'by': 'type'})
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'nonmedia', 'test.txt')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'audio', 'test.mp3')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'video', 'test.avi')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, 'image', 'test.jpg')))

    def test_organize_by_date(self):
        import datetime
        date_format = '%Y-%m'
        today = datetime.date.today()
        year_month = today.strftime(date_format)

        self._run_organize({'by': 'date', 'date_format': date_format})
        
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, year_month, 'test.txt')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, year_month, 'test.mp3')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, year_month, 'test.avi')))
        self.assertTrue(os.path.exists(os.path.join(self.test_dir, year_month, 'test.jpg')))

    def test_organize_by_type_with_target_dir(self):
        target_dir = os.path.join(self.test_dir, 'organized_by_type')
        os.makedirs(target_dir)
        self._run_organize({'by': 'type', 'target_dir': target_dir})
        self.assertTrue(os.path.exists(os.path.join(target_dir, 'nonmedia', 'test.txt')))
        self.assertTrue(os.path.exists(os.path.join(target_dir, 'audio', 'test.mp3')))
        self.assertTrue(os.path.exists(os.path.join(target_dir, 'video', 'test.avi')))
        self.assertTrue(os.path.exists(os.path.join(target_dir, 'image', 'test.jpg')))

if __name__ == '__main__':
    unittest.main()
