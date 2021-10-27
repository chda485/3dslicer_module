import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
import cv2
import os
from matplotlib.image import imsave
from PIL.ImageQt import ImageQt
from PIL import Image, ImageOps, ImageEnhance

SliderStyle = """
QSlider::add-page:vertical {
    background: white;
}

QSlider::sub-page:vertical {
    background: pink;
}
"""

class Example(QtWidgets.QWidget):
    def __init__(self, voxels, background, slices, percents):
        super().__init__()
        self.background = background #массив картинок фона
        self.slices = slices #массив обработанных картинок срезов
        self.percents = percents #массив процентов поражения
        #copy() используем так как обнаружено, что происходят изменения в массивах, чьи значения присваиваются
        #этим изменения мешали настроить окна визуализации
        self.voxels = voxels.copy() #массив картинок фона для корректной работы окон визуализации
        self.temp_voxel = None #массив для хранения изменённых значений HU
        self.current_slice = None #номер отображаемого среза
        self.current_mask = None #отображаемая маска обработанного среза
        self.x_cor = None #текущие х-координаты курсора
        self.y_cor = None #текущие у-координаты курсора
        #self.min_v = np.amin(self.voxels) #минимальное значение HU
        #self.max_v = np.amax(self.voxels) #максимальное значение HU
        self.top_point = 0 #верхняя граница окна визуализации
        self.low_point = -1200 #нижняя граница окна визуализации
        self.factor_contrast = 1
        self.factor_bright = 1
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

        self.fat_s = np.around(self.percents, 4)
        self.fat_s *= 100.0

        self.slider.setMaximum(self.background.shape[0] - 1)
        mask = self.slices[0].copy()
        #делаем изображения маски обработанного среза полупрозрачным делением значений пикселей на 3
        mask[:,:,] = mask[:,:,] // 3

        back = Image.fromarray(self.background[0].copy())

        enhancer = ImageEnhance.Brightness(back)
        image = enhancer.enhance(self.factor_bright)

        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(self.factor_contrast)

        image = np.asarray(image)

        self.current_slice = 0
        self.current_mask = mask
        
        #добавляем маску на фоновую картинку и делаем серым
        img = cv2.add(image, mask)
        
        img = Image.fromarray(img)
        qt = ImageQt(img)
        transformed = QtGui.QPixmap.fromImage(qt)
        #используем grayscale8 так как больше не найдено способа вставить серое изображение как картинку в pyqt5
        #image = QtGui.QImage(img, img.shape[1], img.shape[0],
        #                              QtGui.QImage.Format_Grayscale8)
        #transformed = image.convertToFormat(QtGui.QImage.Format_Grayscale8)
        self.pixmap = QtGui.QPixmap(transformed)
        self.label.setPixmap(self.pixmap)

        self.percent.setText("%.2f %%" % (self.fat_s[0]))
        self.show()

    def changeValue(self, value):
        mask = self.slices[value].copy()
        #делаем изображения маски обработанного среза полупрозрачным делением значений пикселей на 3
        mask[:,:,] = mask[:,:,] // 3

        self.temp_voxel = self.voxels[value]
        image = self.make_image_from_hu(self.temp_voxel)

        image = Image.fromarray(image)
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(self.factor_bright)

        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(self.factor_contrast)

        image = np.asarray(image)

        self.background[value] = image
        back = self.background[value].copy()
        self.current_slice = value
        self.current_mask = mask
        #добавляем маску на фоновую картинку и делаем серым
        img = cv2.add(back, mask)
        
        img = Image.fromarray(img)
        qt = ImageQt(img)
        transformed = QtGui.QPixmap.fromImage(qt)
        # используем grayscale8 так как больше не найдено способа вставить серое изображение как картинку в pyqt5
        #image = QtGui.QImage(img, img.shape[1], img.shape[0],
        #                             QtGui.QImage.Format_Grayscale8)
        #transformed = image.convertToFormat(QtGui.QImage.Format_Grayscale8)
        self.pixmap = QtGui.QPixmap(transformed)
        self.label.setPixmap(self.pixmap)
        self.percent.setText("%.2f %%" % (self.fat_s[value]))
        
    def mouseMoveEvent(self, event):
        #проверяем, нажата ли средняя кнопка
        if event.buttons() & QtCore.Qt.MidButton:
            #если курсор только появился в области изображения, то ничего пока не делаем
            if self.x_cor is None:
                self.x_cor = event.x()
                return
            if self.y_cor is None:
                self.y_cor = event.y()
            #используем для расчётов исходные срезы из 3D Slicer
            #для того, чтобы получались корректные окна визуализации 
            #и легче считались значения HU в определённых точках
            #(например, чтобы при расширени окна знать конкретные значения точки до сужения)
            self.temp_voxel = self.voxels[self.current_slice].copy()
            temp = self.make_image_from_hu(self.temp_voxel)
            temp = Image.fromarray(temp)
            #высчитываем перемещение по координатам
            dX = event.x() - self.x_cor
            dY = event.y() - self.y_cor
            self.x_cor = event.x()
            self.y_cor = event.y()
            #изменяем ширину окна. Если движение вправо, то раздвигаем границы на 1 HU
            #вверх и вниз. Иначе сужаем на алогичную величину
            
            if dX > 0:
                self.factor_contrast += 0.01                
            else:
                self.factor_contrast -= 0.01 
            """    
            if dY > 0:
                self.factor_bright += 0.01                
            else:
                self.factor_bright -= 0.01
            """    
            enhancer = ImageEnhance.Contrast(temp)
            image = enhancer.enhance(self.factor_contrast)
            enhancer = ImageEnhance.Brightness(image)
            image = enhancer.enhance(self.factor_bright)
            #изменяем уровень окна. Если движение вверх, то понижаем уровень на 1 HU
            #иначе повышаем на аналогичную величину
            #print("dX - {}, contrast - {}, brightness - {}".format(dX, self.factor_contrast, self.factor_bright))
            image = np.asarray(image)

            img = cv2.add(image, self.current_mask)
                
            img = Image.fromarray(img)
            qt = ImageQt(img)
            transformed = QtGui.QPixmap.fromImage(qt)
            #используем grayscale8 так как больше не найдено способа вставить серое изображение как картинку в pyqt5
            #image = QtGui.QImage(img, img.shape[1], img.shape[0],
            #                              QtGui.QImage.Format_Grayscale8)
            #transformed = image.convertToFormat(QtGui.QImage.Format_Grayscale8)
            self.pixmap = QtGui.QPixmap(transformed)
            self.label.setPixmap(self.pixmap)

    def make_image_from_hu(self, hu):
        image = (np.maximum(hu, 0) / hu.max()) * 255.0
        image = np.uint8(image)
        return image



