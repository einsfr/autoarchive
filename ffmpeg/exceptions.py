# FFmpeg


class FFmpegBinaryNotFound(FileNotFoundError):
    pass


class FFmpegProcessException(Exception):
    pass


class FFmpegInputNotFoundException(FileNotFoundError):
    pass


class FFmpegOutputAlreadyExistsException(FileExistsError):
    pass

# FFprobe


class FFprobeBinaryNotFound(FileNotFoundError):
    pass


class FFprobeProcessException(Exception):
    pass


class FFprobeTerminatedException(Exception):
    pass
