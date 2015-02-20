import unittest
import tests.commons.test_commons
import tests.ffmp.test_ffmp_utils
import tests.ffmp.test_ffmp_tools
import tests.fs.test_fsutils
import tests.tags.test_tag_tools

def batch_mp_test_suite():

    loader = unittest.TestLoader()
    batch_mp_test_suite = unittest.TestSuite()

    # load tests from the commons package
    commons_suite = loader.loadTestsFromModule(tests.commons.test_commons)

    # load tests from the ffmp package
    ffmp_utils_suite = loader.loadTestsFromModule(tests.ffmp.test_ffmp_utils)
    ffmp_tools_suite = loader.loadTestsFromModule(tests.ffmp.test_ffmp_tools)

    # load tests from the fs package
    fstools_utils_suite = loader.loadTestsFromModule(tests.fs.test_fsutils)

    # load tests from the tags package
    tags_suite = loader.loadTestsFromModule(tests.tags.test_tag_tools)


    batch_mp_test_suite.addTests(commons_suite)
    batch_mp_test_suite.addTests(ffmp_utils_suite)
    batch_mp_test_suite.addTests(ffmp_tools_suite)
    batch_mp_test_suite.addTests(fstools_utils_suite)
    batch_mp_test_suite.addTests(tags_suite)

    return batch_mp_test_suite
