import unittest
import tests.ffmp.test_ffmp_utils as utils
import tests.ffmp.test_ffmp_tools as tools
import tests.fs.test_fstools as fstools

def batch_mp_test_suite():

    loader = unittest.TestLoader()
    batch_mp_test_suite = unittest.TestSuite()

    # load tests from the ffmp package
    ffmp_utils_suite = loader.loadTestsFromModule(utils)
    ffmp_tools_suite = loader.loadTestsFromModule(tools)

    # load tests from the fstools package
    loader = unittest.TestLoader()
    fstools_utils_suite = loader.loadTestsFromModule(fstools)


    batch_mp_test_suite.addTests(ffmp_utils_suite)
    #batch_mp_test_suite.addTests(ffmp_tools_suite)
    batch_mp_test_suite.addTests(fstools_utils_suite)

    return batch_mp_test_suite
