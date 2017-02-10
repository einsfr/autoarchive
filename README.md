# autoarchive
Automatic batch processor for media archiving purposes written entirely in Python (>=3.5). Parses input file or directory and performs some action (one or many) with every file found according to rules set. Each rule in rules set contains a regular expression (for input filename match checking), an action name and some action parameters.

## Supported rules set formats
* JSON

## Supported actions
### ffmpeg
Processes a file with ffmpeg. Ffmpeg and ffprobe binaries are required and must be installed separately. See FFmpeg project's official site: [ffmpeg.org](https://ffmpeg.org)). Calls ffprobe to gather input file metadata (width, height, codec, etc...) and [Jinja2](http://jinja.pocoo.org/) template engine to use it in conversion profiles.

