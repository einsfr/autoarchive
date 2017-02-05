class FFmpegBinaryNotFound(FileNotFoundError):
    pass


class FFmpegProcessException(Exception):
    pass


class FFprobeBinaryNotFound(FileNotFoundError):
    pass


class FFprobeProcessException(Exception):
    pass


class FFprobeTerminatedException(Exception):
    pass
