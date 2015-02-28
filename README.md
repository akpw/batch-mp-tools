
#Description
Python CLI tools for batch processing of media files


**Status:**
A weekend project under occasional development :)

    
##Blogs
- [Parallel batch media processing with FFmpeg and Python](http://arseniy.drupalgardens.com/content/parallel-batch-media-processing-ffmpeg-and-python)


##Requirements
- [Python 3.x](https://www.python.org/download/releases/3.4.1/)


##Install
**Standard install**
- via [pip](https://pip.pypa.io/en/latest/):
```pip install git+https://github.com/akpw/batch-mp-tools.git```
- Or, clone the repo and run:
```python setup.py install```

**Development version**
- Clone the repo, then run: ```python setup.py develop```

**Running Tests**
- Run via: ```python setup.py test```

##CLI Commands
###renamer
    Batch renaming of files and directories
    . visualises original / targeted folders structure before actual rename action
    . supports recursion to specified end level
    . supports flattening folders beyond end level
    . directory print 'slicing', from a given start level to specified end_level
    . allows for include / exclude patterns (Unix style)
    . display sorting:
        .. by size/date, ascending/descending
    . action commands:
        .. print source directory
        .. flatten folders below target level (moves the files up the target level)
        .. regexp-based replace
        .. add index
        .. add date
        .. add text 
        .. remove n characters

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

###tagger
    Batch management of media files metadata (tags & artwork)
    . Supported formats:
        'MP3', 'MP4', 'M4A', 'AIFF', 'ASF', 'QuickTime / MOV',
        'FLAC', 'MonkeysAudio', 'Musepack',
        'Ogg FLAC', 'Ogg Speex', 'Ogg Theora', 'Ogg Vorbis',
        'True Audio', 'WavPack', 'OptimFROG'

        'AVI', 'FLV', 'MKV', 'MKA' (support via FFmpeg)

    . source directory / source file modes
    . include / exclude patterns, etc. (see list of Global Options for details)
    . visualises original / targeted files metadata structure
    . action commands:
        .. print metadata info
        .. set metadata tags
        .. copy tags from a given media file
        .. remove all tags
        .. index tracks
        .. TBD: extracts artwork
        .. TBD: add / remove characters in tags (title, artist, ...)
        .. TBD: regexp-based replace in tags (title, artist, ...)

    Usage: tagger {-d DIR} [GLobal Options] {Commands}[Commands Options]
      Global Options (renamer -h for additional help)
        [-e END_LEVEL]                        End level for recursion into nested folders
        [-i INCLUDE] [-e EXCLUDE]             Include names pattern
        [-fd FILTER_DIRS] [-ff FILTER_FILES]  Use Include/Exclude patterns on dirs / files
        [-s SORT]                             Sorting for files / folders
        [-q QUIET]                            Do not visualise / show messages during processing
        
      tagger -h for additional help on global options

      Commands (tagger {command} -h for additional help)
      {print, set, copy, remove, index}
        print   Print media directory
        set     Set tags in media files
        copy    Copies tags from a specified media file
        remove  Remove all tags
        index   Index Track / Track Total tags for selected media files

      tagger {command} -h for additional help
        
        
###bmp
    Batch processing of media files
    . Uses multiprocessing to utilize available CPU cores
    . source directory / source file modes
    . recursion to specified end_level
    . include / exclude patterns, etc. (see list of Global Options for details)
    . action commands:
        .. denoise
        .. split
        .. speed up
        .. slow down
        .. adjust volume
        .. convert

    Usage: bmp [-h] [-d DIR] [-f FILE] [GLobal Options] {Commands}[Commands Options]
      Global Options (bmp -h for additional help)
        [-e END_LEVEL]                        End level for recursion into nested folders
        [-i INCLUDE] [-e EXCLUDE]             Include names pattern
        [-fd FILTER_DIRS] [-ff FILTER_FILES]  Use Include/Exclude patterns on dirs / files
        [-s SORT]                             Sorting for files / folders
        [-q QUIET]                            Do not visualise / show messages during processing
    
      bmp -h for additional help on global options
    
      Commands: (bmp {command} -h for additional help)
      {denoise, split, speedup, slowdown, volume, convert}
        denoise   Reduces background audio noise in media files
                      via filtering out highpass / low-pass frequencies
        split     TDB: Splits media files
        speedup   TDB: Uses Time Stretching to increase audio / video speed
        slowdown  TDB: Uses Time Stretching to decrease audio / video speed
        volume    TDB: Adjust audiot volume
        convert   TDB: Convert media to specified format

      bmp {Command} -h for additional help





