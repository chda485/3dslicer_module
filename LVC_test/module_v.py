import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
import cv2


SliderStyle = """
QSlider::add-page:vertical {
    background: white;
}

QSlider::sub-page:vertical {
    background: pink;
}
"""

class Example(QtWidgets.QWidget):
    def __init__(self, background, slices, percents):
        super().__init__()
        self.background = background
        self.slices = slices
        self.percents = percents
        self.current_slice = None
        self.current_mask = None
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
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.percent.setFont(font)
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(170, 170, 127))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(170, 170, 127))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
        self.setPalette(palette)
        self.setWindowTitle("Оценка поражения при COVID-19")

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
        mask[:,:,] = mask[:,:,] // 3
          
        back = self.background[0].copy()
        self.current_slice = back
        self.current_mask = mask
        
        img = cv2.add(back, mask)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        image = QtGui.QImage(img, img.shape[1], img.shape[0],
                                      QtGui.QImage.Format_Grayscale8)
        transformed = image.convertToFormat(QtGui.QImage.Format_Grayscale8)
        self.pixmap = QtGui.QPixmap(transformed)
        self.label.setPixmap(self.pixmap)

        self.percent.setText("%.2f %%" % (self.fat_s[0]))
        self.show()

    def changeValue(self, value):
        mask = self.images[value].copy()
        mask[:,:,] = mask[:,:,] // 3
        
        back = self.background[value].copy()
        self.current_slice = back
        self.current_mask = mask
        
        img = cv2.add(back, mask)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        image = QtGui.QImage(img, img.shape[1], img.shape[0],
                                      QtGui.QImage.Format_Grayscale8)
        transformed = image.convertToFormat(QtGui.QImage.Format_Grayscale8)
        self.pixmap = QtGui.QPixmap(transformed)
        self.label.setPixmap(self.pixmap)
        self.percent.setText("%.2f %%" % (self.fat_s[value]))
        
    def wheelEvent(self, e):
        angle = e.angleDelta() / 8
        img = self.current_slice
        img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
        h,s,v = cv2.split(img)
        if angle.y() == 15:
            lim = 5
            v[v >= lim] -= 5
            v[v < lim] = 0
        elif angle.y() == -15:            
            lim = 255 - 5
            v[v > lim] = 255
            v[v <= lim] += 5
            
        final = cv2.merge((h,s,v))
        img = cv2.cvtColor(final, cv2.COLOR_HSV2BGR)
        
        self.current_slice = img
        
        img2 = cv2.add(img, self.current_mask)
        img = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
            
        image = QtGui.QImage(img, img.shape[1], img.shape[0],
                                      QtGui.QImage.Format_Grayscale8)
        transformed = image.convertToFormat(QtGui.QImage.Format_Grayscale8)
        self.pixmap = QtGui.QPixmap(transformed)
        self.label.setPixmap(self.pixmap)



