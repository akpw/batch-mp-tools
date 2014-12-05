import unittest
import tests.ffmp.test_ffmp_utils
import tests.ffmp.test_ffmp_tools
import tests.fs.test_fsutils

def batch_mp_test_suite():

    loader = unittest.TestLoader()
    batch_mp_test_suite = unittest.TestSuite()

    # load tests from the ffmp package
    ffmp_utils_suite = loader.loadTestsFromModule(tests.ffmp.test_ffmp_utils)
    ffmp_tools_suite = loader.loadTestsFromModule(tests.ffmp.test_ffmp_tools)

    # load tests from the fs package
    loader = unittest.TestLoader()
    fstools_utils_suite = loader.loadTestsFromModule(tests.fs.test_fsutils)


    batch_mp_test_suite.addTests(ffmp_utils_suite)
    #batch_mp_test_suite.addTests(ffmp_tools_suite)
    batch_mp_test_suite.addTests(fstools_utils_suite)

    return batch_mp_test_suite
