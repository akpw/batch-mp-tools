#FFmpeg batch runner

Requires Python 3.x

src/ffmptools
--------------
  A Python package for running batch FFmpeg commands
  
  Uses Python multiprocessing to leverage available CPU cores
  
  Supports recursive processing of media files in all subdirectoris
  
  Supports multi-passes processing, e.g. 3 times for each media file in a source dir
  
  Supports backing up original media in their respective folders
  
  Displays continuos progress

Scripts
--------
 src/denoiser.py
 
  Reduces background audio noise in media files via filtering out highpass / low-pass frequencies
  
  Usage: denoiser.py -d DIR [-r] [-n NUM_PASSES] [-hp HIGH_PASS] [-lp LOW_PASS] [-nb] [-q] [-h]
  
    ('denoiser.py -h' for help)

Install
-------
  . Copy the content of src dir to your hard drive
  
  . Run the scripts from there
  
  . Or, add the scripts location to your PATH (export PATH="<path to scripts>:$PATH")

