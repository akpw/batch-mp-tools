
#Description
Python CLI tools for batch processing of media files


**Status:**
A rainy-weekends project under occasional development :)


The project consists of three main tools.
[Renamer](https://github.com/akpw/batch-mp-tools#renamer) primarily takes care of shaping up files names, supporting various batch rename operations as well as flattening folders and cleaning up non-relevant files.

[Tagger](https://github.com/akpw/batch-mp-tools#tagger) manages media metadata, such as tags and artwork. Setting those in selected media file over multiple nested directories now becomes a breeze, with just a few simple commands working uniformly over almost any imaginable media formats. While being simple at its core, Tagger also provides support for advanced metadata manipulation such as template processing, regexp-based replace in selected tags, etc.

[BMFP](https://github.com/akpw/batch-mp-tools#bmfp) is all about effecient media content processing, such as conversion between various formats, segmenting / fragmenting media files, denoising audio, detauching individual audio / video streams, etc. As processing media files can typically be resouce-consuming, BMFP is designed to take advantage of nowdays common multi-core processors, breaking up jobs into individual tasks that are then run a separate processes on separate CPU cores.


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
      . visualises original / targeted folders structure before actual processing
      . supports recursion to specified end_level
      . supports flattening folders beyond specified end_level
      . allows for include / exclude patterns (Unix style)
      . allows global include/exclude of directories and folders
      . display sorting:
          .. by size/date, ascending/descending
      . action commands:
          .. print      Prints source directory
          .. flatten    Flatten all folders below target level, moving the files up
                            at the target level. By default, deletes all empty flattened folders
          .. index      Adds index to files and directories names
          .. add_date   Adds date to files and directories names
          .. add_text   Adds text to files and directories names
          .. remove     Removes n characters from files and directories names
          .. replace    RegExp-based replace in files and directories names
          .. capitalize Capitalizes words in files / directories names
          .. delete     Delete selected files and directories

    Usage: renamer [-h] [-d DIR] [-f FILE] [GLobal Options] {Commands}[Commands Options]
        [-d, --dir]                 Source directory (default is the current directory)
        [-f, --file]                File to process

      Global Options (renamer -h for additional help)
        [-r, --recursive]           Recurse into nested folders
        [-el, --end-level]          End level for recursion into nested folders

        [-in, --include]            Include names pattern (Unix style)
        [-ex, --exclude]            Exclude names pattern (Unix style)
        [-ad, --all-dirs]           Prevent using Include/Exclude patterns on directories
        [-af, --all-files]          Prevent using Include/Exclude patterns on files

        [-s, --sort]{na|nd|sa|sd}   Sort order for files / folders (name | date, asc | desc)
        [-ni, nested-indent]        Indent for printing nested directories
        [-q, --quiet]               Do not visualise changes / show messages during processing

      Commands (renamer {command} -h for additional help)
        {print, flatten, index, add_date, add_text, remove, replace, capitalize, delete}

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
          .. print      Prints media info
          .. set        Sets tags in media files, including artwork, e.g:
                                $ tagger set --album 'The Album' -art '~/Desktop/art.jpg'
                            Supports expandable templates. To specify a template value,
                            use the long tag field name preceded by $:
                                $ tagger set --title '$title, $track of $tracktotal'
                            In addition to tag fields templates, file names are also supported:
                                $ tagger set --title '$filename'...
          .. copy       Copies tags from a specified media file
          .. index      Indexes Track / Track Total tags
          .. remove     Removes tags from media files
          .. replace    RegExp-based replace in specified tags
                          e.g., to remove the first three characters in title:
                                $ tagger replace -tf 'title' -fs '^[\s\S]{0,3}' -rs ''
          .. capitalize Capitalizes words in specified tags
          .. detauch    Extracts artwork

    Usage: tagger [-h] [-d DIR] [-f FILE] [GLobal Options] {Commands}[Commands Options]
        [-d, --dir]                 Source directory (default is the current directory)
        [-f, --file]                File to process

      Global Options (tagger -h for additional help)
        [-r, --recursive]           Recurse into nested folders
        [-el, --end-level]          End level for recursion into nested folders

        [-in, --include]            Include names pattern (Unix style)
        [-ex, --exclude]            Exclude names pattern (Unix style)
        [-ad, --all-dirs]           Prevent using Include/Exclude patterns on directories
        [-af, --all-files]          Prevent using Include/Exclude patterns on files

        [-s, --sort]{na|nd|sa|sd}   Sort order for files / folders (name | date, asc | desc)
        [-ni, nested-indent]        Indent for printing nested directories
        [-q, --quiet]               Do not visualise changes / show messages during processing

      Commands (tagger {command} -h for additional help)
        {print, set, copy, index, remove, replace, capitalize, detauch}

###bmfp
    Batch processing of media files
      . Uses multiprocessing to utilize available CPU cores
      . supports source directory / source file modes
      . supports recursion to specified end_level
      . allows for include / exclude patterns (Unix style)
      . action commands:
          .. convert        Converts media to specified format
          .. segment        Splits media files into segments
                                For example, to split media files in segments of 45 mins:
                                    $ bmfp segment -d 45:00
          .. fragment       Extract a media file fragment
          .. denoise        Reduces background audio noise in media files
          .. speed up       TDB: Uses Time Stretching to increase audio / video speed
          .. slow down      TDB: Uses Time Stretching to increase audio / video speed
          .. adjust volume  TDB: Adjust audio volume

    Usage: bmfp [-h] [-d DIR] [-f FILE] [GLobal Options] {Commands}[Commands Options]
        [-d, --dir]                 Source directory (default is the current directory)
        [-f, --file]                File to process

      Global Options (bmfp -h for additional help)
        [-r, --recursive]           Recurse into nested folders
        [-el, --end-level]          End level for recursion into nested folders

        [-in, --include]            Include names pattern (Unix style)
        [-ex, --exclude]            Exclude names pattern (Unix style)
        [-ad, --all-dirs]           Prevent using Include/Exclude patterns on directories
        [-af, --all-files]          Prevent using Include/Exclude patterns on files

        [-s, --sort]{na|nd|sa|sd}   Sort order for files / folders (name | date, asc | desc)
        [-q, --quiet]               Do not visualise changes / show messages during processing

        [-ma, --map-all]            Force including all streams from the input file
        [-cc, --copy-codecs]        Copy streams codecs without re-encoding
        [-vn, --no-video]           Exclude video streams from the output
        [-an, --no-audio]           Exclude audio streams from the output
        [-sn, --no-subs]            Exclude subtitles streams from the output
        [-fo, --ffmpeg-options]     Additional FFmpeg options

        [-pm, --preserve-meta]      Preserve metadata of processed files
        [-se, --serial-exec]        Run all task's commands in a single process
        [-nb, --no-backup]          Do not backup the original file

      Commands: (bmfp {command} -h for additional help)
        {convert, denoise, fragment, segment, ...}





