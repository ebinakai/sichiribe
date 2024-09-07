from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QPushButton, QLabel, QSlider
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPixmap
from gui.utils.screen_manager import ScreenManager
from gui.utils.common import convert_cv_to_qimage, gen_graph
from gui.workers.live_detect_worker import DetectWorker
from gui.workers.export_worker import ExportWorker
import logging
import numpy as np

class LiveExeWindow(QWidget):
    def __init__(self, screen_manager: ScreenManager):
        super().__init__()
        
        self.screen_manager = screen_manager
        screen_manager.add_screen('live_exe', self)
        
        self.logger = logging.getLogger('__main__').getChild(__name__)
        self.initUI()

    def initUI(self):
        # レイアウトを作成
        main_layout = QVBoxLayout()
        graph_layout = QVBoxLayout()
        extracted_image_layout = QHBoxLayout()
        form_layout = QFormLayout()
        footer_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # レイアウトの設定
        graph_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        extracted_image_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # グラフの設定
        self.graph_label = QLabel()
        graph_layout.addWidget(self.graph_label)
        
        # 選択領域表示用レイアウト
        self.extracted_label = QLabel()
        self.extracted_label.setMinimumHeight(100)
        extracted_image_layout.addWidget(self.extracted_label)
        
        # しきい値設定
        slider_layout = QHBoxLayout()  # 水平レイアウトを作成
        self.binarize_th = QSlider()
        self.binarize_th.setFixedWidth(200)
        self.binarize_th.setRange(0, 255)
        self.binarize_th.setOrientation(Qt.Orientation.Horizontal)
        self.binarize_th.valueChanged.connect(self.update_binarize_th)
        self.binarize_th_label = QLabel()
        slider_layout.addWidget(self.binarize_th)  # スライダーを追加
        slider_layout.addWidget(self.binarize_th_label)  # ラベルを追加
        form_layout.addRow("画像二値化しきい値：", slider_layout)   # そのレイアウトをaddRowに渡す

        # フッターレイアウト
        # グラフクリアボタン
        self.graph_clear_button = QPushButton('グラフクリア')
        self.graph_clear_button.setFixedWidth(100)
        self.graph_clear_button.clicked.connect(self.graph_clear)
        
        # 中止ボタン
        self.term_label = QLabel()
        self.term_label.setStyleSheet('color: red')
        self.term_button = QPushButton('途中終了')
        self.term_button.setFixedWidth(100)
        self.term_button.clicked.connect(self.cancel)
        
        footer_layout.addWidget(self.graph_clear_button)
        footer_layout.addStretch()  # スペーサー
        footer_layout.addWidget(self.term_label)
        footer_layout.addWidget(self.term_button)
        
        # メインレイアウトに追加
        main_layout.addLayout(graph_layout)
        main_layout.addLayout(extracted_image_layout)
        main_layout.addLayout(form_layout)
        main_layout.addStretch()
        main_layout.addLayout(footer_layout)
        
    def cancel(self):
        if self.worker is not None:
            self.term_label.setText('中止中...')
            self.worker.cancel()  # ワーカーに停止を指示
            
    def update_binarize_th(self, value):
        value = None if value == 0 else value
        binarize_th_str = '自動設定' if value is None else str(value)
        self.binarize_th_label.setText(binarize_th_str)
        if self.worker is not None:
            self.worker.update_binarize_th(value)
    
    def graph_clear(self):
        self.graph_results = []
        self.graph_failed_rates = []
        self.graph_timestamps = []
        self.update_graph(self.results[-1], self.failed_rates[-1], self.timestamps[-1])
    
    def startup(self, params):
        self.logger.info('Starting LiveExeWindow.')
        self.screen_manager.get_screen('log').clear_log()
        self.screen_manager.show_screen('log')
        
        # ウィンドウの位置とサイズを保存
        window_pos, window_size = self.screen_manager.save_screen_size()
     
        # 初期化
        self.binarize_th.setValue(0)
        self.binarize_th_label.setText('自動設定')
        self.term_label.setText('')
        self.params = params
        self.results = []
        self.failed_rates = []
        self.timestamps = []
        self.graph_results = []
        self.graph_failed_rates = []
        self.graph_timestamps = []
        self.worker = DetectWorker(self.params)
        self.worker.progress.connect(self.update_graph)
        self.worker.send_image.connect(self.display_extract_image)
        self.worker.end.connect(self.detect_finished)
        self.worker.cancelled.connect(self.detect_cancelled)
        self.worker.model_not_found.connect(self.model_not_found)
        self.worker.start()
        self.logger.info('Detect started.')
        
    def model_not_found(self):
        self.term_label.setText('モデルが見つかりません')
        self.logger.error('Model not found.')
        self.clear_env()
        QTimer.singleShot(1, lambda: self.screen_manager.show_screen('menu'))
        
    def update_graph(self, result, failed_rate, timestamp):
        self.screen_manager.show_screen('live_exe')
        self.results.append(result)
        self.failed_rates.append(failed_rate)
        self.timestamps.append(timestamp)
        
        # グラフの更新
        self.graph_results.append(result)
        self.graph_failed_rates.append(failed_rate)
        self.graph_timestamps.append(timestamp)
        title = 'Results'
        xlabel = 'Frame'
        ylabel1 = 'Failed Rate'
        ylabel2 = 'Detected results'
        graph = gen_graph(self.graph_timestamps, self.graph_failed_rates, self.graph_results, title, xlabel, ylabel1, ylabel2, self.screen_manager.check_if_dark_mode())

        # QLabel に画像を設定
        q_image = convert_cv_to_qimage(graph)
        self.graph_label.setPixmap(QPixmap.fromImage(q_image))
        
    def display_extract_image(self, image: np.ndarray):
        q_image = convert_cv_to_qimage(image)
        self.extracted_label.setPixmap(QPixmap.fromImage(q_image))
        
    def detect_finished(self):
        self.logger.info('Detect finished.')
        self.logger.info(f"Results: {self.results}")
        self.params['results'] = self.results
        self.params['failed_rates'] = self.failed_rates
        self.params['timestamps'] = self.timestamps
        params = self.params
        self.clear_env()
        QTimer.singleShot(1, lambda: self.export_process(params))
        
    def detect_cancelled(self):
        self.term_label.setText('中止しました')
        self.logger.info('Detect cancelled.')
        self.logger.info(f"Results: {self.results}")
        self.params['results'] = self.results
        self.params['failed_rates'] = self.failed_rates
        self.params['timestamps'] = self.timestamps
        params = self.params
        self.clear_env()
        QTimer.singleShot(1, lambda: self.export_process(params))

    def export_process(self, params):
        self.params = params
        self.logger.info('Export started.')
        self.worker = ExportWorker(self.params)
        self.worker.finished.connect(self.export_finished)
        self.worker.start()

    def export_finished(self):
        self.logger.info('Export finished.')
        self.screen_manager.get_screen('finish').startup(self.params)
        self.params = None
   
    def clear_env(self):
        self.graph_label.clear()
        self.extracted_label.clear()
        self.term_label.setText('')
        self.params = None
        self.results = None
        self.failed_rates = None
        self.timestamps = None
        self.graph_results = None
        self.graph_failed_rates = None
        self.graph_timestamps = None
        self.logger.debug("Environment cleared.")
        
        # ウィンドウサイズを元に戻す
        # QTimer.singleShot(1, self.screen_manager.restore_screen_size)
    