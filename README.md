
**Status:**
A rainy weekends project under occasional development :)

####Requirements:
- [Python 3.4.x](https://www.python.org/download/releases/3.4.1/) or later

####Install:
- from [PyPI](https://pypi.python.org/pypi/batchmp): `$ pip install batchmp`
- latest from source repository: `$ pip install git+https://github.com/akpw/batch-mp-tools.git`

####Blogs:
- [The Batch-MP-Tools Project](http://arseniy.drupalgardens.com/content/batch-mp-tools-project)
- [Parallel batch media processing with FFmpeg and Python](http://arseniy.drupalgardens.com/content/parallel-batch-media-processing-ffmpeg-and-python)

##Description

Batch management of media files, from base properties such as file names through tags / artwork metadata to advanced operations on the media content.

The project is written in [Python 3.4](https://www.python.org/download/releases/3.4.1/) and currently consists of three main command-line utilities. All three share the core concept of various transformations applied to generated stream of selected file system entries, and consequently they also share the same set of global options. A quick way to check on that is to run:
```
    $ renamer -h
    $ tagger -h
    $ bmfp -h
```
That will show the global options along with specific commands for each tool. Getting more info on the commands level can be done using a similar approach, e.g. to learn more about the `renamer index` command:
```
    $ renamer index -h
```
By default the tools always visualize targeted changes (whenever possible) before actual processing.

A little bit more details on each utility:

[**Renamer**](https://github.com/akpw/batch-mp-tools#renamer) is a multi-platform batch rename tool. In addition to common operations such as regexp-based replace, adding text / dates, etc. it also supports advanced operations such as multi-level indexing across nested directories, flattening folders, and cleaning up non-media files.
At its simplest, Renamer can be used to print out the content of current directory:
```
    $ renamer
```
Without command arguments, renamer uses `print` as the default command. A little bit more advanced, if perhaps you'd like to see what's lurking at the 7th nested folder level:
```
    $ renamer print -sl 7
```
Or, how about multi-level indexing of all M4A files in all sub-directories of the current folder:
```
    $ renamer -r -in '*.m4a' index
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
```
Sequential indexing is supported as well using the `-sq` switch.  An important detail here, by default Renamer is visualizing the targeted changes and asking for permission to proceed before actually doing anything.



[**Tagger**](https://github.com/akpw/batch-mp-tools#tagger) manages media metadata, such as tags and artwork. Setting those in selected media file over multiple nested directories now becomes a breeze, with just a few simple commands working uniformly over almost any imaginable media formats. While easy to use, Tagger also supports advanced metadata manipulation such as regexp-based replace, template processing, etc. For example, to set the title tag to respective file names followed by the values of track and tracktotal tags:
```
    $ tagger -r -in '*BWV816 1*' set --title '$filename, $track of $tracktotal'
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
```
The commands above show some of the available global options:  `-r` for recursion into nested folders and `-in` to select media files (just one here, for the sake of output brevity).


[**BMFP**](https://github.com/akpw/batch-mp-tools/blob/master/README.md#bmfp-requires-ffmpeg) is all about efficient media content processing, such as conversion between various formats, segmenting / fragmenting media files, denoising audio, detaching individual audio / video streams, etc. As processing media files can typically be resource consuming, BMFP is designed to take advantage of multi-core processors. By default, it automatically breaks up jobs into individual tasks that are then run as separate processes on CPU cores.
**BMFP is built on top of [FFmpeg](http://ffmpeg.org/download.html), which needs to be installed and available in the command line**. BMFP can be thought of as a batch FFmpeg runner, intended to make common uses of FFmpeg extremely easy while not restricting its full power.

For example, to convert all files from the above example from M4A to FLAC:
```
    $ bmfp -r -pm convert -la -tf FLAC
```
The `-pm` switch here forces preserving *all* metadata information, while `-la` explicitly tells BMFP to do a lossless conversion.

To check on the result, lets's just use the [tagger](https://github.com/akpw/batch-mp-tools#tagger) ability to print media files info:
```
    $ tagger -r -in '*BWV816 1*' print -st -ss
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
```
From a brief glance, all looks OK and the tags seem to be preserved as well. As its default behaviour, BMFP also backed up the original file and replace it with the converted one.

I will follow up with more examples and common use-cases in future blogs.


##Full description of CLI Commands
###renamer
    Batch renaming of files and directories
      . visualises original / targeted folders structure before actual processing
      . supports recursion (also can go down to explicitly specified end_level)
      . supports flattening folders beyond specified target_level
      . allows for include / exclude patterns (Unix style)
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
      Input source mode:
        [-d, --dir]                 Source directory (default is the current directory)
        [-f, --file]                File to process

      Recursion mode:
        [-r, --recursive]           Recurse into nested folders
        [-el, --end-level]          End level for recursion into nested folders

      Filter files or folders:
        [-in, --include]            Include: Unix-style name patterns separated by ';'
        [-ex, --exclude]            Exclude: Unix-style name patterns separated by ';'
        [-fd, --filter-dirs]        Enable  Include/Exclude patterns on directories
        [-af, --all-files]          Disable Include/Exclude patterns on files

      Miscellaneous:
        [-s, --sort]{na|nd|sa|sd}   Sort order for files / folders (name | date, asc | desc)
        [-ni, nested-indent]        Indent for printing nested directories
        [-q, --quiet]               Do not visualise changes / show messages during processing

      Commands:
        {print, flatten, index, add_date, add_text, remove, replace, capitalize, delete}
        $ renamer {command} -h  #run this for detailed help on individual commands

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
      Input source mode:
        [-d, --dir]                 Source directory (default is the current directory)
        [-f, --file]                File to process

      Recursion mode:
        [-r, --recursive]           Recurse into nested folders
        [-el, --end-level]          End level for recursion into nested folders

      Filter files or folders:
        [-in, --include]            Include: Unix-style name patterns separated by ';'
        [-ex, --exclude]            Exclude: Unix-style name patterns separated by ';'
        [-fd, --filter-dirs]        Enable  Include/Exclude patterns on directories
        [-af, --all-files]          Disable Include/Exclude patterns on files

      Miscellaneous:
        [-s, --sort]{na|nd|sa|sd}   Sort order for files / folders (name | date, asc | desc)
        [-ni, nested-indent]        Indent for printing nested directories
        [-q, --quiet]               Do not visualise changes / show messages during processing

      Commands:
        {print, set, copy, index, remove, replace, capitalize, detauch}
        $ tagger {command} -h #run this for detailed help on individual commands

###bmfp (requires [FFmpeg](http://ffmpeg.org/download.html))
    Batch processing of media files
      . Uses multiprocessing to utilize available CPU cores
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
      Input source mode:
        [-d, --dir]                 Source directory (default is the current directory)
        [-f, --file]                File to process

      Recursion mode:
        [-r, --recursive]           Recurse into nested folders
        [-el, --end-level]          End level for recursion into nested folders

      Filter files or folders:
        [-in, --include]            Include: Unix-style name patterns separated by ';'
        [-ex, --exclude]            Exclude: Unix-style name patterns separated by ';'
        [-fd, --filter-dirs]        Enable  Include/Exclude patterns on directories
        [-af, --all-files]          Disable Include/Exclude patterns on files

      Miscellaneous:
        [-q, --quiet]               Do not visualise changes / show messages during processing

      FFmpeg General Options:
        [-ma, --map-all]            Force including all streams from the input file
        [-cc, --copy-codecs]        Copy streams codecs without re-encoding
        [-vn, --no-video]           Exclude video streams from the output
        [-an, --no-audio]           Exclude audio streams from the output
        [-sn, --no-subs]            Exclude subtitles streams from the output
        [-fo, --ffmpeg-options]     Additional FFmpeg options

      FFmpeg Commands Execution:
        [-pm, --preserve-meta]      Preserve metadata of processed files
        [-se, --serial-exec]        Run all task's commands in a single process
        [-nb, --no-backup]          Do not backup the original file

      Commands:
        {convert, denoise, fragment, segment, ...}
        $ bmfp {command} -h  #run this for detailed help on individual commands

##Installing Development version
- Clone the repo, then run: `$ python setup.py develop`

**Running Tests**
- Run via: `$ python setup.py test`






