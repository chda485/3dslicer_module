import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
import cv2, sys
from PIL import Image
#from matplotlib import image as image_reader
#import qt

SliderStyle = """
QSlider::add-page:vertical {
    background: white;
}

QSlider::sub-page:vertical {
    background: pink;
}
"""

class Example(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.background = np.load(r"F:\initial.npy")
        self.slices = np.load(r"F:\all.npy")
        self.percents = np.load(r"F:\fat_s.npy")
        self.initUI()

    def initUI(self):
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider.setStyleSheet(SliderStyle)
        self.slider.setGeometry(120, 600, 290, 20)
        self.slider.setMinimum(0)
        self.slider.valueChanged[int].connect(self.changeValue)
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(60, 40, 512, 512)
        self.percent = QtWidgets.QLineEdit(self)
        self.percent.setGeometry(490, 600, 70, 20)
        self.percent.setEnabled(False)

        """убираем все полностью белые картинки"""
        self.images = [x for x in self.slices if np.count_nonzero(x == 0) != 0]
        self.images = np.asarray(self.images)
        """делаем массив с индексами убранных картинок"""
        indices = [index for index, x in enumerate(self.slices) if np.count_nonzero(x == 0) == 0]
        indices = np.asarray(indices)
        """убираем картинки с индексами убранных слайсов толстых структур"""
        self.initial = [x for i, x in enumerate(self.background) if i not in indices]
        self.background = np.asarray(self.initial)

        self.fat_s = [x for i, x in enumerate(self.percents) if i not in indices]
        self.fat_s = np.around(self.fat_s, 4)
        self.fat_s *= 100.0

        self.slider.setMaximum(self.images.shape[0] - 1)
        mask = self.images[0].copy()
        back = self.background[0].copy()
        img = cv2.add(back, mask)
        img = cv2.cvtColor(back, cv2.COLOR_BGR2GRAY)

        image = QtGui.QImage(img, img.shape[1], img.shape[0],
                                      QtGui.QImage.Format_Grayscale8)
        #transformed = image.convertToFormat(QtGui.QImage.Format_Grayscale8)
        self.pixmap = QtGui.QPixmap(image)
        self.label.setPixmap(self.pixmap)

        self.percent.setText("{} %".format(self.fat_s[184]))
        self.show()

    def changeValue(self, value):
        mask = self.images[value].copy()
        back = self.background[value].copy()
        img = cv2.add(back, mask)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        image = QtGui.QImage(img, img.shape[1], img.shape[0],
                                      QtGui.QImage.Format_Grayscale8)
        #transformed = image.convertToFormat(QtGui.QImage.Format_Grayscale8)
        self.pixmap = QtGui.QPixmap(image)
        self.label.setPixmap(self.pixmap)
        self.percent.setText("%.2f %%" % (self.fat_s[value]))

def show():
    app = QtWidgets.QApplication(sys.argv)
    ex = Example()
    #ex.show()
    sys.exit(app.exec_())
show()


