
#Description
Python CLI tools for batch processing of media files


**Status:**
A rainy-weekends project under occasional development :)


##Blogs
- [Parallel batch media processing with FFmpeg and Python](http://arseniy.drupalgardens.com/content/parallel-batch-media-processing-ffmpeg-and-python)


##Requirements
- [Python 3.4.x](https://www.python.org/download/releases/3.4.1/)


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
      . supports source directory / source file modes
      . visualises original / targeted folders structure before actual rename action
      . supports recursion to specified end_level
      . supports flattening folders beyond end_level
      . can print directory from given a start_level to specified end_level
      . allows for include / exclude patterns (Unix style)
      . allows global include/exclude of directories and folders
      . display sorting:
          .. by size/date, ascending/descending
      . action commands:
          .. print      Prints source directory
          .. flatten    Flatten all folders below target level, moving the files up
                            at the target level. By default, deletes all empty flattened folders
          .. index      Adds index to files and directories
          .. date       Adds date to files and directories
          .. text       Adds text to files and directories
             remove     Removes n characters from files and directories
             replace    RegExp-based replace in files and directories

    Usage: renamer [-h] [-d DIR] [-f FILE] [GLobal Options] {Commands}[Commands Options]
        [-d, --dir]                 Source directory (default is the current directory)
        [-f, --file]                File to process

      Global Options (renamer -h for additional help)
        [-r, --recursive]           Recurse into nested folders
        [-el, --endlevel]           End level for recursion into nested folders
        [-in, --include]            Include names pattern (Unix style)
        [-ex, --exclude]            Exclude names pattern (Unix style)
        [-ad, --alldirs]            Prevent using Include/Exclude patterns on directories
        [-af, --allfiles]           Prevent using Include/Exclude patterns on files
        [-s, --sort]{na|nd|sa|sd}   Sort order for files / folders (name | date, asc | desc)
        [-q, --quiet]               Do not visualise changes / show messages during processing

      Commands (renamer {command} -h for additional help)
        {print, flatten, index, date, text, remove,replace}

###tagger
    Batch management of media files metadata (tags & artwork)
      . Supported formats:
            'MP3', 'MP4', 'M4A', M4V', 'AIFF', 'ASF', 'QuickTime / MOV',
            'FLAC', 'MonkeysAudio', 'Musepack',
            'Ogg FLAC', 'Ogg Speex', 'Ogg Theora', 'Ogg Vorbis',
            'True Audio', 'WavPack', 'OptimFROG'

            'AVI', 'FLV', 'MKV', 'MKA' (support via FFmpeg)
      . source directory / source file modes
      . include / exclude patterns, etc. (see list of Global Options for details)
      . visualises original / targeted files metadata structure
      . action commands:
          .. print      print media info
          .. set        Set tags in media files,
                        Supports expandable templates:
                          e.g.  <tagger set --title 'The Title, part $track of $tracktotal'>
                          to specify a template value, use the long tag name preceded by $:
                                <tagger set --album 'The Album, ($format)'>, ...
          .. copy       Copies tags from a specified media file
          .. remove     Remove all tags
          .. index      Index Track / Track Total tags
          .. add        TBD: add characters in tags (title, artist, ...)
          .. remove     TBD: remove characters in tags (title, artist, ...)
          .. replace    TBD: regexp-based replace in tags (title, artist, ...)
          .. extract    TBD: extracts artwork

    Usage: tagger [-h] [-d DIR] [-f FILE] [GLobal Options] {Commands}[Commands Options]
        [-d, --dir]                 Source directory (default is the current directory)
        [-f, --file]                File to process

      Global Options (tagger -h for additional help)
        [-r, --recursive]           Recurse into nested folders
        [-el, --endlevel]           End level for recursion into nested folders
        [-in, --include]            Include names pattern (Unix style)
        [-ex, --exclude]            Exclude names pattern (Unix style)
        [-ad, --alldirs]            Prevent using Include/Exclude patterns on directories
        [-af, --allfiles]           Prevent using Include/Exclude patterns on files
        [-s, --sort]{na|nd|sa|sd}   Sort order for files / folders (name | date, asc | desc)
        [-q, --quiet]               Do not visualise changes / show messages during processing

      Commands (tagger {command} -h for additional help)
        {print, set, copy, remove, index, ...}

###bmfp
    Batch processing of media files
      . Uses multiprocessing to utilize available CPU cores
      . supports source directory / source file modes
      . supports recursion to specified end_level
      . allows for include / exclude patterns (Unix style)
      . action commands:
          .. convert        Converts media to specified format
          .. segment        Splits media files into segments
          .. fragment       Extract a media file fragment
          .. denoise        Reduces background audio noise in media files
          .. speed up       TDB: Uses Time Stretching to increase audio / video speed
          .. slow down      TDB: Uses Time Stretching to increase audio / video speed
          .. adjust volume  TDB: Adjust audio volume
          .. detauch        TDB: Detauch streams from original media

    Usage: bmfp [-h] [-d DIR] [-f FILE] [GLobal Options] {Commands}[Commands Options]
        [-d, --dir]                 Source directory (default is the current directory)
        [-f, --file]                File to process

      Global Options (bmfp -h for additional help)
        [-r, --recursive]           Recurse into nested folders
        [-el, --endlevel]           End level for recursion into nested folders
        [-in, --include]            Include names pattern (Unix style)
        [-ex, --exclude]            Exclude names pattern (Unix style)
        [-ad, --alldirs]            Prevent using Include/Exclude patterns on directories
        [-af, --allfiles]           Prevent using Include/Exclude patterns on files
        [-s, --sort]{na|nd|sa|sd}   Sort order for files / folders (name | date, asc | desc)
        [-q, --quiet]               Do not visualise changes / show messages during processing

        [-fo, --ffmpeg-options]     Additional options for running FFmpeg
        [-pm, --preserve-meta]      Preserve metadata of processed files
        [-se, --serial-exec]        Run all task's commands in a single process
        [-nb, --no-backup]          Do not backup the original file

      Commands: (bmfp {command} -h for additional help)
        {convert, denoise, fragment, segment, ...}





