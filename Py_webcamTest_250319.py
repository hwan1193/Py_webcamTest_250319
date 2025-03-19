from __future__ import annotations

import os
import sys
import time

import cv2
from PySide6.QtCore import Qt, QThread, Signal, Slot
from PySide6.QtGui import QAction, QImage, QKeySequence, QPixmap
from PySide6.QtWidgets import (QApplication, QComboBox, QGroupBox,
                               QHBoxLayout, QLabel, QMainWindow, QPushButton,
                               QSizePolicy, QVBoxLayout, QWidget, QMenuBar, QMenu, QMessageBox)


class Thread(QThread):
    updateFrame = Signal(QImage)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.trained_file = None
        self.status = True
        self.cap = True

        # 동영상 녹화 관련
        self.recording = False
        self.video_writer = None

    def set_file(self, fname):
        # The data comes with the 'opencv-python' module
        self.trained_file = os.path.join(cv2.data.haarcascades, fname)

    def start_recording(self, filename="output.avi"):
        """동영상 녹화를 시작하는 함수."""
        # fourcc 설정 (XVID, MJPG 등)
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        # 초당 프레임 수, 해상도는 간단히 640x480, FPS=20 가정
        self.video_writer = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))
        self.recording = True

    def stop_recording(self):
        """동영상 녹화를 중지하는 함수."""
        self.recording = False
        if self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None

    def run(self):
        self.cap = cv2.VideoCapture(0)
        while self.status:
            cascade = cv2.CascadeClassifier(self.trained_file)
            ret, frame = self.cap.read()
            if not ret:
                continue

            # Reading frame in gray scale to process the pattern
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            detections = cascade.detectMultiScale(
                gray_frame,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )

            # Drawing green rectangle around the pattern
            for (x, y, w, h) in detections:
                pos_ori = (x, y)
                pos_end = (x + w, y + h)
                color = (0, 255, 0)
                cv2.rectangle(frame, pos_ori, pos_end, color, 2)

            # (추가) 동영상 녹화 중이면, 원본 frame을 파일로 기록
            if self.recording and self.video_writer is not None:
                self.video_writer.write(frame)

            # Reading the image in RGB to display it
            color_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Creating and scaling QImage
            h, w, ch = color_frame.shape
            img = QImage(color_frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
            scaled_img = img.scaled(640, 480, Qt.AspectRatioMode.KeepAspectRatio)

            # Emit signal
            self.updateFrame.emit(scaled_img)

        sys.exit(-1)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        # Title and dimensions
        self.setWindowTitle("Patterns detection")
        self.setGeometry(0, 0, 800, 500)

        # Main menu bar
        self.menu = self.menuBar()
        self.menu_file = self.menu.addMenu("File")
        exit_action = QAction("Exit", self, triggered=self.close)
        self.menu_file.addAction(exit_action)

        self.menu_about = self.menu.addMenu("&About")
        about = QAction("About Qt", self,
                        shortcut=QKeySequence(QKeySequence.StandardKey.HelpContents),
                        triggered=self.about_qt)
        self.menu_about.addAction(about)

        # Create a label for the display camera
        self.label = QLabel(self)
        self.label.setFixedSize(640, 480)

        # Thread in charge of updating the image
        self.th = Thread(self)
        self.th.finished.connect(self.close)
        self.th.updateFrame.connect(self.setImage)

        # Model group
        self.group_model = QGroupBox("Trained model")
        self.group_model.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        model_layout = QHBoxLayout()

        self.combobox = QComboBox()
        for xml_file in os.listdir(cv2.data.haarcascades):
            if xml_file.endswith(".xml"):
                self.combobox.addItem(xml_file)

        model_layout.addWidget(QLabel("File:"), 10)
        model_layout.addWidget(self.combobox, 90)
        self.group_model.setLayout(model_layout)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        self.button_start = QPushButton("Start")
        self.button_stop = QPushButton("Stop/Close")
        self.button_start.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.button_stop.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        # (추가) 녹화 관련 버튼
        self.button_record = QPushButton("Record")
        self.button_stop_record = QPushButton("Stop Record")
        self.button_record.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
        self.button_stop_record.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        buttons_layout.addWidget(self.button_stop)
        buttons_layout.addWidget(self.button_start)
        buttons_layout.addWidget(self.button_record)
        buttons_layout.addWidget(self.button_stop_record)

        right_layout = QHBoxLayout()
        right_layout.addWidget(self.group_model, 1)
        right_layout.addLayout(buttons_layout, 1)

        # Main layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addLayout(right_layout)

        # Central widget
        widget = QWidget(self)
        widget.setLayout(layout)
        self.setCentralWidget(widget)

        # Connections
        self.button_start.clicked.connect(self.start_thread)
        self.button_stop.clicked.connect(self.kill_thread)
        self.button_stop.setEnabled(False)
        self.combobox.currentTextChanged.connect(self.set_model)

        # (추가) 녹화 버튼 시그널 연결
        self.button_record.clicked.connect(self.start_recording)
        self.button_stop_record.clicked.connect(self.stop_recording)
        self.button_stop_record.setEnabled(False)

    @Slot()
    def about_qt(self):
        QMessageBox.aboutQt(self, "About Qt")

    @Slot()
    def set_model(self, text):
        self.th.set_file(text)

    @Slot()
    def kill_thread(self):
        print("Finishing...")
        self.button_stop.setEnabled(False)
        self.button_start.setEnabled(True)
        self.th.cap.release()
        cv2.destroyAllWindows()
        self.th.stop_recording()  # 녹화 중이면 중지
        self.th.recording = False
        self.th.status = False
        self.th.terminate()
        # Give time for the thread to finish
        time.sleep(1)

    @Slot()
    def start_thread(self):
        print("Starting...")
        self.button_stop.setEnabled(True)
        self.button_start.setEnabled(False)
        self.th.set_file(self.combobox.currentText())
        self.th.start()

    @Slot()
    def start_recording(self):
        """녹화 시작 버튼 클릭 시 호출."""
        self.th.start_recording("C:\Testweb.avi")
        self.button_record.setEnabled(False)
        self.button_stop_record.setEnabled(True)
        print("Recording started...")

    @Slot()
    def stop_recording(self):
        """녹화 중지 버튼 클릭 시 호출."""
        self.th.stop_recording()
        self.button_record.setEnabled(True)
        self.button_stop_record.setEnabled(False)
        print("Recording stopped.")

    @Slot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = Window()
    w.show()
    sys.exit(app.exec())