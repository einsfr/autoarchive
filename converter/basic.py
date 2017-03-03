from dispatcher.basic import BasicDispatcher


class BasicConverter:

    def __init__(self, input_url: str, profile: str, conf_out_dir: str, use_in_dir_as_root: bool, simulate: bool):
        self._dispatcher = BasicDispatcher(
            input_url,
            {
                'policy': 'error',
                'patterns': [['*', {}, 'ffmpeg.convert', {'profile': profile}]],
            },
            conf_out_dir, 0, use_in_dir_as_root, simulate
        )

    def convert(self):
        self._dispatcher.dispatch()
