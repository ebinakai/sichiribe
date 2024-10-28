from tensorflow.keras.models import load_model
from cores.cnn import CNNCore
import os
import logging
from typing import TYPE_CHECKING
import numpy as np
from pathlib import Path

# TensorFlow と h5py のログを無効にする
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
logging.getLogger('tensorflow').setLevel(logging.ERROR)
logging.getLogger('h5py').setLevel(logging.ERROR)

if TYPE_CHECKING:
    from tensorflow.keras.models import Model


class CNNTf(CNNCore):
    model: "Model"

    def __init__(self, num_digits: int,
                 model_filename: str) -> None:
        super().__init__(num_digits)
        self.logger = logging.getLogger("__main__").getChild(__name__)

        # 学習済みモデルの絶対パスを取得
        current_dir = Path(__file__).resolve().parent
        model_path = current_dir / '..' / 'model' / model_filename
        model_path = model_path.resolve()
        self.model_path = str(model_path)
        self.logger.debug('Load model path: %s' % self.model_path)

        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        self.model = load_model(self.model_path)
        self.logger.info("CNN Model loaded.")

    def inference_7seg_classifier(self, image):
        # 各桁に分割
        preprocessed_images = self.preprocess_image(image)

        predictions = self.model.predict(
            np.array(preprocessed_images),
            verbose=0)  # verbose=0: ログ出力を抑制

        argmax_indices = predictions.argmax(axis=1)  # 各行に対して最大値のインデックスを取得

        return argmax_indices
