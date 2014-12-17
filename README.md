
#Description
Python package for batch processing of media files


#Status
A weekend project under occasional development :)

    
#Blogs 
[Parallel batch media processing with FFmpeg and Python](http://arseniy.drupalgardens.com/content/parallel-batch-media-processing-ffmpeg-and-python)


#Requirements
    . Python 3.x


#Install
####With [pip](https://pip.pypa.io/en/latest/):
"pip install git+https://github.com/akpw/batch-mp-tools.git"

Or, clone the repo and run: "python setup.py install"

####Development version
Clone the repo, then run "python setup.py develop"

####Tests
Run via "python setup.py test"


#Scripts
###denoiser
    . requires FFmpeg (http://ffmpeg.org)
    . Reduces background audio noise in media files via filtering out highpass / low-pass frequencies
    . Uses Python multiprocessing to leverage available CPU cores
    . Supports recursive processing of media files in subfolders
    . Supports multi-passes processing, e.g. 3 times for each media file in a source dir
    . Supports backing up original media in their respective folders
    . Displays continuos progress
    . Usage: denoiser -d DIR [-r] [-n NUM_PASSES] [-hp HIGH_PASS] [-lp LOW_PASS] [-nb] [-q] [-h]
        ('denoiser.py -h' for help)
        
###renamer
    Batch renaming of files and directories
    . visualises original / targeted folders structure before actual rename action
    . supports recursion to specified end_level
    . supports flattening folders beyond end_level
    . can print directory from given a start_level to specified end_level
    . allows for include / exclude patterns (Unix style)
    . allows global include/exclude of directories and folders
    . display sorting:
        .. by size/date, ascending/descending
    . action commands:
        .. print source directory
        .. regexp-based replace
        .. add index
        .. add date
        .. add text
        .. remove n characters
        .. flatten all folders below target level, moving the files
           up the target level. 

    Usage: renamer -d DIR [GLobal Options] {Commands}[Commands Options]
    
      Global Options (renamer -h for additional help)
        [-e END_LEVEL]                        End level for recursion into nested folders
        [-i INCLUDE] [-e EXCLUDE]             Include names pattern
        [-fd FILTER_DIRS] [-ff FILTER_FILES]  Use Include/Exclude patterns on dirs / files
        [-s SORT]                             Sorting for files / folders
        [-q QUIET]                            Do not visualise / show messages during processing
        
      Commands: 
        {print, flatten, index, date, text, remove,replace}
        
    More Info:  
        "renamer -h" for additional help on global options
        "renamer <command> -h" for additional help on specific commands





