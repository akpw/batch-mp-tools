
**Status:**
A rainy weekends project under occasional development :)

####Requirements:
- [Python 3.4.x](https://www.python.org/download/releases/3.4.1/) or later

####Install:
- from [pypi](https://pypi.python.org/pypi/batchmp): ```$ pip install batchmp```
- latest from source repository: ``` $ pip install git+https://github.com/akpw/batch-mp-tools.git```

####Blogs:
- [The Batch-MP-Tools Project](http://arseniy.drupalgardens.com/content/batch-mp-tools-project)
- [Parallel batch media processing with FFmpeg and Python](http://arseniy.drupalgardens.com/content/parallel-batch-media-processing-ffmpeg-and-python)

##Description

Batch management of media files, starting from base properties such as file names through tags / artwork metadata to various manipulation of the media content.

The project is written in [Python 3.4](https://www.python.org/download/releases/3.4.1/), and currently available as a command line utility. It  consists of three main tools, sharing the same concept of visualizing targeted changes (whenever possible) before actual processing.

[Renamer](https://github.com/akpw/batch-mp-tools#renamer) primarily takes care of shaping up files names, supporting various batch rename operations as well as indexing, flattening folders, and cleaning up non-relevant files. For example, to index M4A files in all sub-directories of the current folder:
````
    $ renamer -r -in '*.m4a' -ad index
    /Desktop/_test/Gould
      |-/1
        |- 01 Glenn Gould French Suite 1 In D, BWV812 1 Allemande.m4a
        |- 02 Glenn Gould French Suite 1 In D, BWV812 2 Courante.m4a
        |- 03 Glenn Gould French Suite 1 In D, BWV812 3 Sarabande.m4a
      |-/2
        |- 01 Bach, Johann Sebastian French Suite 5 In G Major, BWV816 1 Allemande.m4a
        |- 02 Bach, Johann Sebastian French Suite 5 In G Major, BWV816 2 Courante.m4a
        |- 03 Bach, Johann Sebastian French Suite 5 In G Major, BWV816 3 Sarabande.m4a
      |-/_Art
    6 files, 3 folders
    
    Proceed? [y/n]:    
````
An important detail here, by default Renamer is visualizing the targeted changes and asking for permission to proceed before actually doing anything.



[Tagger](https://github.com/akpw/batch-mp-tools#tagger) manages media metadata, such as tags and artwork. Setting those in selected media file over multiple nested directories now becomes a breeze, with just a few simple commands working uniformly over almost any imaginable media formats. While being simple at its core, Tagger also provides support for advanced metadata manipulation such as regexp-based replace, template processing, etc. For example, to set the title tag to respective file name followed by the values of track and tracktotal tags:
````
    $ tagger -r -in '*BWV816 1*' -ad set --title '$filename, $track of $tracktotal'
    Targeted after processing:
    /Desktop/_test/Gould
      |-/1
      |-/2
        |- Bach, Johann Sebastian French Suite 5 In G Major, BWV816 1 Allemande.m4a
        	Title: Bach, Johann Sebastian French Suite 5 In G Major, BWV816 1 Allemande, 1 of 26
        	Album: Bach French Suites BWV 812-817 Vol. II; Glenn Gould
        	Artist: Glenn Gould
        	Album Artist: Glenn Gould
        	Genre: Classical
        	Composer: Johann Sebastian Bach (1685-1750)
        	Year: 1994
        	Track: 1/26
        	Disk: 2/2
      |-/Art
    1 files, 3 folders  
    
    Proceed? [y/n]: n
````
The commands above show some of the available global options:  ```-r``` for recursion into nested folders and ```-in``` to select media files (just one here, for the sake of output brevity). The ```-ad``` switch force looking in all sub-directores, without filtering them by the ```-in``` pattern. 
As all three tools share the core concept of various transformations applied to generated stream of file systems entries, they also share the same set of global options. A quick way to check on that is to run: 
```
    $ renamer -h
    $ tagger -h
    $ bmfp -h
``` 
That will show all global options along with specific commands for each tool. Getting more info on the commands level can be done using a similar approach, e.g. to learn more about the renamer index command: 
```
    $ renamer index -h
```



[BMFP](https://github.com/akpw/batch-mp-tools/blob/master/README.md#bmfp-requires-ffmpeg) is all about efficient media content processing, such as conversion between various formats, segmenting / fragmenting media files, denoising audio, detaching individual audio / video streams, etc. As processing media files can typically be resource consuming BMFP is designed to take advantage of multi-core processors, breaking up jobs into individual tasks that are then run as separate processes on individual CPU cores. BMFP is built on top of [FFmpeg](http://ffmpeg.org/download.html), *which needs to be installed and available in the command line*. 
For example, to convert the file from previous example from M4A to FLAC:
````
    $ bmfp -r -in '*BWV816 1*' -ad -pm convert -la -tf FLAC
````
The ```-pm``` switch forces preserving all metadata information, while ```-la``` explicitly tells BMFP to try a lossless conversion. 

To check on the result, lets's just use the tagger abilities to print media files info:
````
    $ tagger -r -in '*BWV816 1*' -ad print -st -ss -h
    /Users/AKPower/Desktop/_test/Gould
      |-/1
      |-/2
        |-  7.4MB Bach, Johann Sebastian French Suite 5 in G major, BWV816 1 Allemande.flac
        	Title: French Suite 5 in G major, BWV 816 - 1 Allemande
        	Album: Bach French Suites BWV 812-817 Vol. II; Glenn Gould
        	Artist: Glenn Gould
        	Album Artist: Glenn Gould
        	Genre: Classical
        	Composer: Johann Sebastian Bach (1685-1750)
        	Year: 1994
        	Track: 1/26
        	Disk: 2/2
        	Format: FLAC
        	Duration: 0:01:48, Bit rate: 548kb/s, Sample rate: 44100Hz, Bit depth: 16
        |-/_backup_15Mar25_094341
          |-  7.9MB Bach, Johann Sebastian French Suite 5 in G major, BWV816 1 Allemande.m4a
          	Title: French Suite 5 in G major, BWV 816 - 1 Allemande
          	Album: Bach French Suites BWV 812-817 Vol. II; Glenn Gould
          	Artist: Glenn Gould
          	Album Artist: Glenn Gould
          	Genre: Classical
          	Composer: Johann Sebastian Bach (1685-1750)
          	Year: 1994
          	Track: 1/26
          	Disk: 2/2
          	Format: ALAC
          	Duration: 0:01:48, Bit rate: 579kb/s, Sample rate: 44100Hz, Bit depth: 16
      |-/Art
    2 files, 4 folders
    Total size: 15.2MB
````
From a brief glance, looks OK and the tags seem to be preserved as well. As a default behaviour, BMFP also backed up the original file and replace it with the converted one.

I will follow up with more examples and common use-cases in future blogs.


##Full description of CLI Commands 
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

###bmfp (requires [FFmpeg](http://ffmpeg.org/download.html))
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

##Installing Development version
- Clone the repo, then run: ```$ python setup.py develop```

**Running Tests**
- Run via: ```$ python setup.py test```






