
#Description

    . Python package for batch processing of media files
    
    . Blog: [Parallel batch media processing with FFmpeg and Python](http://arseniy.drupalgardens.com/content/parallel-batch-media-processing-ffmpeg-and-python)


#Install
    . A standard install via "python setup.py install"
    

#Requirements

    . Python 3.x 
    . FFmpeg [installed](http://ffmpeg.org/download.html)


#Scripts
Intended to provide convinient CLI interface


###denoiser
    . Reduces background audio noise in media files via filtering out highpass / low-pass frequencies

    . Uses Python multiprocessing to leverage available CPU cores

    . Supports recursive processing of media files in subfolders

    . Supports multi-passes processing, e.g. 3 times for each media file in a source dir

    . Supports backing up original media in their respective folders

    . Displays continuos progress
    
    . Usage: denoiser -d DIR [-r] [-n NUM_PASSES] [-hp HIGH_PASS] [-lp LOW_PASS] [-nb] [-q] [-h]

        ('denoiser.py -h' for help)







