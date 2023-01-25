
**Status:**
A rainy weekends project under occasional development :)

#### Requirements:
- [Python 3.4.x](https://www.python.org/download/releases/3.4.1/) or later

#### Install:
- from [PyPI](https://pypi.python.org/pypi/batchmp): `$ pip install batchmp`
- latest from source repository: `$ pip install git+https://github.com/akpw/batch-mp-tools.git`

#### Blogs:
- [Practical BatchMP](http://www.akpdev.com/tags.html#BatchMP+Tools)
- [BatchMP Tools Tutorial](http://www.akpdev.com/articles/2015/04/10/batchmp-tutorial-part-i.html)
- [The BatchMP Tools Project](http://www.akpdev.com/articles/2015/03/21/the-batchmp-project.html)
- [Parallel batch media processing with FFmpeg and Python](http://www.akpdev.com/articles/2014/11/24/batch-media-processing-ffmpeg-python.html)

## Description

Batch management of media files, from base properties such as file names through tags / artwork metadata to advanced operations on the media content.

The project is written in [Python 3.4](https://www.python.org/download/releases/3.4.1/) and currently consists of three main command-line utilities. All three share the core concept of various transformations applied to generated stream of file system entries, and consequently they also share the same set of global options. A quick way to check on that is to run:
```
    $ renamer -h
    $ tagger -h
    $ bmfp -h
```
That will show the global options along with specific commands for each tool. Getting more info on the commands level can be done using a similar approach, e.g. to learn more about the `renamer replace` command:
```
    $ renamer replace -h
```
By default the tools always visualize targeted changes (whenever possible) before actual processing.

A little bit more details on each utility:

[**Renamer**](https://github.com/akpw/batch-mp-tools#renamer) is a multi-platform batch rename tool. In addition to common operations such as regexp-based replace, adding text / dates, etc. it also supports advanced operations such as expandable template processing during replace, multi-level indexing across nested directories, flattening folders, and cleaning up non-media files.
At its simplest, Renamer can be used to print out the content of current directory:
```
    $ renamer
```
Without command arguments, renamer uses `print` as the default command. This is also the case for both `$ tagger` and `$ bmfp`, with each of the tool showing info which is relevant to its intended purpose.
A little bit more advanced, to see what's lurking at the 7th nested folder level:
```
    $ renamer print -sl 7
```
For multi-level indexing of all M4A files in all sub-directories of the current folder:
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



[**Tagger**](https://github.com/akpw/batch-mp-tools#tagger) manages media metadata, such as tags and artwork. Setting those in selected media file over multiple nested directories now becomes a breeze, with just a few simple commands working uniformly over almost any practically imaginable audio / video media formats. While easy to use, Tagger supports advanced metadata manipulation such as regexp-based replace, expandable template processing, etc. For example, to set the title tag to respective file names followed by the values of track and tracktotal tags:
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
The commands above show some of the available global options:  `-r` for recursion into nested folders and `-in` to select media files. In the example above just one file was selected (for the sake of output brevity), which also could be achived via using `-f` for the file source mode.


[**BMFP**](https://github.com/akpw/batch-mp-tools/blob/master/README.md#bmfp-requires-ffmpeg) is all about efficient media content processing, such as conversion between various formats, normalizing sound volume, segmenting / fragmenting media files, denoising audio, detaching individual audio / video streams, etc. As processing media files can typically be resource consuming, BMFP is designed to take advantage of multi-core processors. By default, it automatically breaks up jobs into individual tasks that are then run as separate processes on available CPU cores.
**BMFP is built on top of [FFmpeg](http://ffmpeg.org/download.html), which needs to be installed and available in the command line**. BMFP can be thought of as a batch FFmpeg runner, intended to make common uses of FFmpeg easy while not restricting its full power.

For example, to convert all files from the above example from M4A to FLAC:
```
    $ bmfp -r convert -la -tf FLAC
```
The `-tf` switch specifies the target format, while `-la` explicitly tells BMFP to do a lossless conversion.

To check on the result, lets's just use the [tagger's](https://github.com/akpw/batch-mp-tools#tagger) ability to print media files info:
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
From a brief glance, all looks OK. BMFP used FFmpeg to do the actual conversion, while taking care of all other things like preserving tags / artwork, etc.

I will follow up with more examples and common use-cases in future blogs.


## Brief Description of CLI Commands (use -h to expand on details for individual commands)
### renamer
    Batch renaming of files and directories
      . source directory or source file modes
      . visualises original / targeted folders structure before actual processing
      . supports recursion, can optionally stop at specified end_level
      . supports flattening folders beyond specified target_level
      . supports include / exclude patterns (Unix style)
      . display sorting:
          .. by size/date, ascending/descending
      . action commands:
          .. print      Prints source directory
          .. flatten    Flatten all folders below target level, moving the
                        files up at the target level. By default, deletes all empty flattened folders
          .. index      Adds index to files and directories names
          .. replace    RegExp-based replace in files and directories names. Supports expandable templates, 
                        such as $dirname, $pardirname, $atime, $ctime, etc. For media files, also can process 
                        tag-based templates such as $title, $album, $artist, $albumartist, $genre, $year, $track, 
                        etc.
          .. add_date   Adds date to files and directories names
          .. add_text   Adds text to files and directories names
          .. remove     Removes n characters from files and directories names
          .. capitalize Capitalizes words in files / directories names
          .. delete     Delete selected files and directories

    Usage: renamer [-h] [-d DIR] [-f FILE] [Global Options] {Commands} [Commands Options]
    Global Options:
      Input source mode:
        [-d, --dir]                 Source directory (default is the current directory)
        [-f, --file]                File to process

      Recursion mode:
        [-r, --recursive]           Recurse into nested folders
        [-el, --end-level]          End level for recursion into nested folders

      Filter files or folders:
        [-in, --include]            Include: Unix-style name patterns separated by ';'
        [-ex, --exclude]            Exclude: Unix-style name patterns separated by ';'
                                      (excludes hidden files by default)
        [-fd, --filter-dirs]        Enable  Include/Exclude patterns on directories
        [-af, --all-files]          Disable Include/Exclude patterns on files
                                      (shows hidden files excluded by default)
      Miscellaneous:
        [-s, --sort]{na|nd|sa|sd}   Sort order for files / folders (name | date, asc | desc)
        [-ni, nested-indent]        Indent for printing nested directories
        [-q, --quiet]               Do not visualise changes / show messages during processing

      Commands:
        {print, index, add_date, add_text, remove, replace, capitalize, flatten, delete, version, info}
        $ renamer {command} -h  #run this for detailed help on individual commands

### tagger
###### Supported formats:
'MP3', 'MP4', 'M4A', M4V', 'AIFF', 'ASF', 'QuickTime / MOV',
'FLAC', 'MonkeysAudio', 'Musepack',
'Ogg FLAC', 'Ogg Speex', 'Ogg Theora', 'Ogg Vorbis',
'True Audio', 'WavPack', 'OptimFROG' <p>
Support via FFmpeg: 'AVI', 'FLV', 'MKV', 'MKA'

    Batch management of media files metadata (tags & artwork)
      . source directory / source file modes
      . visualises original / targeted files metadata structure
      . supports recursion, can optionally stop at specified end_level
      . include / exclude patterns (Unix style)
      . display sorting:
          .. by size/date, ascending/descending
      . action commands:
          .. print      Prints media info
          .. set        Sets tags in media files, including artwork, e.g:
                                $ tagger set --album 'The Album' -art '~/Desktop/art.jpg'
                            Supports expandable templates. To specify a template value,
                            use the long tag field name preceded by $:
                                $ tagger set --title '$title, $track of $tracktotal'
                            In addition to tag fields templates, file system names are also supported:
                                $ tagger set --title '$filename' --album '$dirname' --artist '$pardirname'...
          .. copy       Copies tags from a specified media file
          .. index      Indexes Track / Track Total tags
          .. remove     Removes tags from media files
          .. replace    RegExp-based replace in specified tags
                          e.g., to remove the first three characters in title:
                                $ tagger replace -tf 'title' -fs '^[\s\S]{0,3}' -rs ''
          .. capitalize Capitalizes words in specified tags
          .. detauch    Extracts artwork

    Usage: tagger [-h] [-d DIR] [-f FILE] [Global Options] {Commands} [Commands Options]
    Global Options:
      Input source mode:
        [-d, --dir]                 Source directory (default is the current directory)
        [-f, --file]                File to process

      Recursion mode:
        [-r, --recursive]           Recurse into nested folders
        [-el, --end-level]          End level for recursion into nested folders

      Filter files or folders:
        [-in, --include]            Include: Unix-style name patterns separated by ';'
        [-ex, --exclude]            Exclude: Unix-style name patterns separated by ';'
                                      (excludes hidden files by default)
        [-fd, --filter-dirs]        Enable  Include/Exclude patterns on directories
        [-af, --all-files]          Disable Include/Exclude patterns on files
                                      (shows hidden files excluded by default)
      Miscellaneous:
        [-s, --sort]{na|nd|sa|sd}   Sort order for files / folders (name | date, asc | desc)
        [-ni, nested-indent]        Indent for printing nested directories
        [-q, --quiet]               Do not visualise changes / show messages during processing

      Commands:
        {print, set, copy, index, remove, replace, capitalize, detauch, version, info}
        $ tagger {command} -h #run this for detailed help on individual commands

### bmfp (requires [FFmpeg](http://ffmpeg.org/download.html))
    Batch processing of media files
      . Uses multiprocessing to utilize available CPU cores
      . source directory / source file modes
      . recursion to specified end_level
      . include / exclude patterns (Unix style)
      . action commands:
          .. print          Prints media files
          .. convert        Converts media to specified format
                                For example, to convert all files in current directory
                                    $ bmfp convert -la -tf FLAC
          .. normalize      Nomalizes sound volume in media files
                                Peak normalization supported, RMS normalizations TBD
          .. fragment       Extract a media file fragment
          .. segment        Splits media files into segments
                                For example, to split media files in segments of 45 mins:
                                    $ bmfp segment -d 45:00
          .. silencesplit   Splits media files into segments via detecting specified silence
                                    $ bmfp silencesplit
          .. cuesplit       Splits media files into parts with specified output format,
                            according to their respective cue sheets
                                For example, to split all cue files in the current directory
                                    $ bmfp cuesplit -tf mp3
          .. denoise        Reduces background audio noise in media files

          .. adjust volume  TDB: Adjust audio volume
          .. speed up       TDB: Uses Time Stretching to increase audio / video speed
          .. slow down      TDB: Uses Time Stretching to increase audio / video speed

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
                                      (excludes hidden files by default)
        [-fd, --filter-dirs]        Enable  Include/Exclude patterns on directories
        [-af, --all-files]          Disable Include/Exclude patterns on files
                                      (shows hidden files excluded by default)

        Target output Directory     Target output directory. When omitted, will be
        [-td, --target-dir]         automatically created at the parent level of
                                    the input source. For recursive processing,
                                    the processed files directory structure there
                                    will be the same as for the original files.
      FFmpeg General Output Options:
        [-ma, --map-all]            Force including all streams from the input file
        [-cc, --copy-codecs]        Copy streams codecs without re-encoding
        [-vn, --no-video]           Exclude video streams from the output
        [-an, --no-audio]           Exclude audio streams from the output
        [-sn, --no-subs]            Exclude subtitles streams from the output
        [-fo, --ffmpeg-options]     Additional FFmpeg options

      FFmpeg Commands Execution:
        [-q, --quiet]               Do not visualise changes / show messages during processing
        [-se, --serial-exec]        Run all task's commands in a single process

      Commands:
        {print, convert, normalize, fragment, segment, silencesplit, cuesplit, denoise, version, info}
        $ bmfp {command} -h  #run this for detailed help on individual commands


## Installing Development version
- Clone the repo, then run: `$ python -m pip install .`

**Running Tests**
- Run via: `$ python setup.py test`






