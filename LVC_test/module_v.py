import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
import cv2
from PIL.ImageQt import ImageQt
from PIL import Image, ImageEnhance

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
        self.background = background #массив картинок фона
        self.slices = slices #массив обработанных картинок срезов
        self.percents = percents #массив процентов поражения
        self.current_slice = None #номер отображаемого среза
        self.current_mask = None #отображаемая маска обработанного среза
        self.factor_contrast = 1
        self.factor_bright = 1
        self.initUI()

    def initUI(self):
        #ползунок прокрутки срезов
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal, self)
        self.slider.setStyleSheet(SliderStyle)
        self.slider.setGeometry(120, 600, 290, 20)
        self.slider.setMinimum(0)
        self.slider.valueChanged[int].connect(self.changeValue)
        #поле для визуализации картинки
        self.label = QtWidgets.QLabel(self)
        self.label.setGeometry(60, 40, 512, 512)
        #поле вывода процента поражения
        self.percent = QtWidgets.QLineEdit(self)
        self.percent.setGeometry(490, 600, 70, 20)
        self.percent.setEnabled(False)
        font = QtGui.QFont()
        font.setFamily("Times New Roman")
        font.setPointSize(12)
        self.percent.setFont(font)
        #заголовки изменения яркости/контраста
        self.bright = QtWidgets.QLabel(self)
        self.bright.setGeometry(610, 450, 80, 40)
        self.bright.setText("Изменение \nяркости")
        self.bright.setFont(font)
        self.contrast = QtWidgets.QLabel(self)
        self.contrast.setGeometry(610, 250, 80, 40)
        self.contrast.setText("Изменение \nконтраста")
        self.contrast.setFont(font)
        #кнопки изменения яркости окна
        font.setPointSize(16)
        self.brightness_down = QtWidgets.QPushButton(self)
        self.brightness_down.setGeometry(600, 500, 40, 40)
        self.brightness_down.setText("<")
        self.brightness_down.clicked.connect(self.bright_down)
        self.brightness_up = QtWidgets.QPushButton(self)
        self.brightness_up.setGeometry(650, 500, 40, 40)
        self.brightness_up.setText(">")
        self.brightness_up.clicked.connect(self.bright_up)
        self.brightness_up.setFont(font)
        self.brightness_down.setFont(font)
        #кнопки изменения контраста окна
        self.contrast_d = QtWidgets.QPushButton(self)
        self.contrast_d.setGeometry(600, 300, 40, 40)
        self.contrast_d.setText("<")
        self.contrast_d.clicked.connect(self.contrast_down)
        self.contrast_u = QtWidgets.QPushButton(self)
        self.contrast_u.setGeometry(650, 300, 40, 40)
        self.contrast_u.setText(">")
        self.contrast_u.clicked.connect(self.contrast_up)
        self.contrast_d.setFont(font)
        self.contrast_u.setFont(font)
        #устанавливаем палитру для изменения фона
        palette = QtGui.QPalette()
        brush = QtGui.QBrush(QtGui.QColor(170, 170, 127))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Window, brush)
        brush = QtGui.QBrush(QtGui.QColor(170, 170, 127))
        brush.setStyle(QtCore.Qt.SolidPattern)
        palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Window, brush)
        self.setPalette(palette)
        self.setWindowTitle("Оценка поражения при COVID-19")
        #округляем значения процентов поражения
        self.fat_s = np.around(self.percents, 4)
        self.fat_s *= 100.0

        self.slider.setMaximum(self.background.shape[0] - 1)
        mask = self.slices[0].copy()
        #делаем изображения маски обработанного среза полупрозрачным делением значений пикселей на 3
        #такое решение выдаёт поиск в интернете
        mask[:,:,] = mask[:,:,] // 3

        #берём начальный срез и преобразуем к пригодному виду для изменения яркости/контраста
        back = Image.fromarray(self.background[0].copy())

        #ставим первоначальный контраст картинки
        enhancer = ImageEnhance.Contrast(back)
        image = enhancer.enhance(self.factor_contrast)
        #ставим первоначальную яркость картинки
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(self.factor_bright)

        #преобразуем в массив для наложения маски 
        image = np.asarray(image)
        self.current_slice = 0
        self.current_mask = mask
        
        #добавляем маску на фоновую картинку
        img = cv2.add(image, mask)
        #создаём объект Image, преобразуем его для вида, пригодного для создания QPixmap
        img = Image.fromarray(img)
        qt = ImageQt(image)
        transformed = QtGui.QPixmap.fromImage(qt)
        self.pixmap = QtGui.QPixmap(transformed)
        self.label.setPixmap(self.pixmap)

        self.percent.setText("%.2f %%" % (self.fat_s[0]))
        self.show()

    def changeValue(self, value):
        mask = self.slices[value].copy()
        #делаем изображения маски обработанного среза полупрозрачным делением значений пикселей на 3
        mask[:,:,] = mask[:,:,] // 3
        #берём тот срез, на номер которого прокрутили ползунок
        img = self.background[value]
        #создаём объект Image для изменения яркости/контраста
        image = Image.fromarray(img)
        
        #меняем контраст картинки
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(self.factor_contrast)
        #меняем яркость картинки
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(self.factor_bright)
        
        #преобразуем в массив для наложения маски 
        image = np.asarray(image)
        self.background[value] = image
        back = self.background[value].copy()
        self.current_slice = value
        self.current_mask = mask
        
        #добавляем маску на фоновую картинку и делаем серым
        img = cv2.add(back, mask)
        #создаём объект Image, преобразуем его для вида, пригодного для создания QPixmap
        img = Image.fromarray(img)
        qt = ImageQt(img)
        transformed = QtGui.QPixmap.fromImage(qt)

        self.pixmap = QtGui.QPixmap(transformed)
        self.label.setPixmap(self.pixmap)
        self.percent.setText("%.2f %%" % (self.fat_s[value]))

    def bright_up(self):
        self.factor_bright += 0.1
        self.update_images()

    def bright_down(self):
        self.factor_bright -= 0.1
        self.update_images()

    def contrast_up(self):
        self.factor_contrast += 0.1
        self.update_images()

    def contrast_down(self):
        self.factor_contrast -= 0.1
        self.update_images()

    def update_images(self):
        # берём срез, который визуализируется в данный момент
        temp = self.background[self.current_slice].copy()
        # создаём объект Image для изменения яркости/контраста
        temp = Image.fromarray(temp)
        # меняем контраст картинки
        enhancer = ImageEnhance.Contrast(temp)
        image = enhancer.enhance(self.factor_contrast)
        # меняем яркость картинки
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(self.factor_bright)

        print("contrast - {}, brightness - {}".format(self.factor_contrast, self.factor_bright))
        # преобразуем в массив для наложения маски
        image = np.asarray(image)
        img = cv2.add(image, self.current_mask)

        # создаём объект Image, преобразуем его для вида, пригодного для создания QPixmap
        img = Image.fromarray(img)
        qt = ImageQt(img)
        transformed = QtGui.QPixmap.fromImage(qt)
        self.pixmap = QtGui.QPixmap(transformed)
        self.label.setPixmap(self.pixmap)

            





