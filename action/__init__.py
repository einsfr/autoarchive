""" Модуль с классами действий для комманды `run`

Новые действия создаются в отдельных подмодулях - по одному для каждого класса с действием. Названия даются так:
- подмодуль называется так же, как название действия, например - `copy`
- класс действия назвается по схеме `<Названиедействия>Action`, например - `CopyAction`
- можно использовать вложенные подмодули - тогда в наборе правил такое действие будет указываться с подмодулем через
  `.`, например - `ffmpeg.convert`, а имя класса будет, соответственно, `FfmpegConvertAction`

"""

import os
import logging

from utils.module_import import get_class


def get_action_class(action_id: str):
    """ Возвращает класс, описывающий действие, по названию этого действия

    Args:
        action_id: название действия

    Returns:
        Класс, описывающий действие
    """
    return get_class('action', action_id)


class AbstractAction:
    """ Базовый абстрактный класс, описывающий действие

    Все классы, описывающие действия, должны наследовать этому классу или его потомкам.
    """

    def run(self, input_url: str, action_params: dict, out_dir_path: str, simulate: bool) -> None:
        """ Запускает выполнение действия

        Если `simulate` равен True, действие не должно вносить никаких изменений в файловую систему, состояние
        приложения - во что угодно. То есть после окончания действия всё должно остаться точно таким же, как было
        до него.

        Args:
            input_url: путь к обрабатываемому файлу
            action_params: параметры действия
            out_dir_path: путь к директории для выходных данных действия
            simulate: флаг симуляции
        """
        raise NotImplementedError


class OutDirCreatingAction(AbstractAction):
    """ Базовый класс для всех действий, которые сами создают структуру папок в `out_dir_path`

    """

    def run(self, input_url: str, action_params: dict, out_dir_path: str, simulate: bool) -> None:
        if not simulate:
            logging.debug('Creating output directory "{}"...'.format(out_dir_path))
            if not simulate:
                os.makedirs(out_dir_path, exist_ok=True)
