import os
import shutil
import logging
import datetime

logger = logging.getLogger("__main__").getChild(__name__)


def clear_directory(directory: str) -> None:
    if not os.path.exists(directory):
        logger.debug(f"The specified directory does not exist: {directory}")
        return

    # ディレクトリ内の全ファイルとサブディレクトリを削除
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            logger.error(f"Failed to delete {file_path}. Reason: {e}")

    logger.debug(
        f"All contents in the directory '{directory}' have been deleted.")


def ask_user_confirmation(prompt: str) -> bool:
    while True:
        answer = input(f"{prompt} (y/n): ").strip().lower()
        if answer in ['y', 'n']:
            return answer == 'y'
        print("Please answer with 'y' or 'n'.")


def get_now_str() -> str:
    return datetime.datetime.now().strftime('%Y%m%d%H%M%S')
