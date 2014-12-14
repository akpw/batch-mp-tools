
#Description
Python package for batch processing of media files


#Status
A weekend project, under development :)
    
    
#Blog 
[Parallel batch media processing with FFmpeg and Python](http://arseniy.drupalgardens.com/content/parallel-batch-media-processing-ffmpeg-and-python)


#Requirements
    . Python 3.x
    . FFmpeg installed


#Install
A standard install via "python setup.py install"


#Tests
Run via "python setup.py test"


#Scripts
###denoiser
    . Reduces background audio noise in media files via filtering out highpass / low-pass frequencies
    . Uses Python multiprocessing to leverage available CPU cores
    . Supports recursive processing of media files in subfolders
    . Supports multi-passes processing, e.g. 3 times for each media file in a source dir
    . Supports backing up original media in their respective folders
    . Displays continuos progress
    . Usage: denoiser -d DIR [-r] [-n NUM_PASSES] [-hp HIGH_PASS] [-lp LOW_PASS] [-nb] [-q] [-h]
        ('denoiser.py -h' for help)







