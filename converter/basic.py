from dispatcher.basic import BasicDispatcher


class BasicConverter:

    def __init__(self, input_url: str, profile: str, profile_vars: list, conf_out_dir: str, dir_depth: int,
                 use_in_dir_as_root: bool, simulate: bool):
        self._dispatcher = BasicDispatcher(
            input_url,
            {
                'policy': 'error',
                'patterns': [['.*', {}, 'ffmpeg.convert', {'profile': profile, 'profile_vars': dict(profile_vars)}]],
            },
            conf_out_dir, dir_depth, use_in_dir_as_root, simulate
        )

    def convert(self):
        self._dispatcher.dispatch()
