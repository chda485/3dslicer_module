import numpy as np
from PyQt5 import QtWidgets, QtCore, QtGui
import cv2
import os
from matplotlib.image import imsave

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
        self.min_v = np.amin(self.voxels) #минимальное значение HU
        self.max_v = np.amax(self.voxels) #максимальное значение HU
        self.top_point = 0 #верхняя граница окна визуализации
        self.low_point = -1200 #нижняя граница окна визуализации
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

        #убираем все полностью белые картинки
        self.images = [x for x in self.slices if np.count_nonzero(x == 0) != 0]
        self.images = np.asarray(self.images)
        #делаем массив с индексами убранных картинок
        indices = [index for index, x in enumerate(self.slices) if np.count_nonzero(x == 0) == 0]
        indices = np.asarray(indices)
        #убираем картинки с индексами убранных слайсов толстых структур
        self.initial = [x for i, x in enumerate(self.background) if i not in indices]
        self.voxels = [x for i, x in enumerate(self.voxels) if i not in indices]
        self.background = np.asarray(self.initial)
        self.voxels = np.asarray(self.voxels)
        #делаем тоже самое для массива процентов поражения, округляем до 4 знаков
        self.fat_s = [x for i, x in enumerate(self.percents) if i not in indices]
        self.fat_s = np.around(self.fat_s, 4)
        self.fat_s *= 100.0

        self.slider.setMaximum(self.images.shape[0] - 1)
        mask = self.images[0].copy()
        #делаем изображения маски обработанного среза полупрозрачным делением значений пикселей на 3
        mask[:,:,] = mask[:,:,] // 3
          
        back = self.background[0].copy()
        self.current_slice = 0
        self.current_mask = mask
        
        #добавляем маску на фоновую картинку и делаем серым
        img = cv2.add(back, mask)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        #используем grayscale8 так как больше не найдено способа вставить серое изображение как картинку в pyqt5
        image = QtGui.QImage(img, img.shape[1], img.shape[0],
                                      QtGui.QImage.Format_Grayscale8)
        transformed = image.convertToFormat(QtGui.QImage.Format_Grayscale8)
        self.pixmap = QtGui.QPixmap(transformed)
        self.label.setPixmap(self.pixmap)

        self.percent.setText("%.2f %%" % (self.fat_s[0]))
        self.show()

    def changeValue(self, value):
        mask = self.images[value].copy()
        #делаем изображения маски обработанного среза полупрозрачным делением значений пикселей на 3
        mask[:,:,] = mask[:,:,] // 3
        
        #проебразуем новое фоновое изображение к текущему установленному окну визуализации
        self.temp_voxel = self.voxels[value].copy()
        self.temp_voxel[self.temp_voxel < self.low_point] = self.min_v
        self.temp_voxel[self.temp_voxel > self.top_point] = self.max_v
        imsave("temp.png", self.temp_voxel)
        self.background[value] = cv2.imread("temp.png")
        back = self.background[value].copy()
        self.current_slice = value
        self.current_mask = mask
        #добавляем маску на фоновую картинку и делаем серым
        img = cv2.add(back, mask)
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        #используем grayscale8 так как больше не найдено способа вставить серое изображение как картинку в pyqt5
        image = QtGui.QImage(img, img.shape[1], img.shape[0],
                                      QtGui.QImage.Format_Grayscale8)
        transformed = image.convertToFormat(QtGui.QImage.Format_Grayscale8)
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
            #высчитываем перемещение по координатам
            dX = event.x() - self.x_cor
            dY = event.y() - self.y_cor
            self.x_cor = event.x()
            self.y_cor = event.y()
            #изменяем ширину окна. Если движение вправо, то раздвигаем границы на 1 HU
            #вверх и вниз. Иначе сужаем на алогичную величину
            if dX > 0:
                self.top_point +=1
                self.low_point -=1
            else:
                self.top_point -=1
                self.low_point +=1
            #изменяем уровень окна. Если движение вверх, то понижаем уровень на 1 HU
            #иначе повышаем на аналогичную величину
            if dY > 0:
                self.top_point -=1
                self.low_point -=1
            else:
                self.top_point +=1
                self.low_point +=1
            #следим, чтобы все значения были в исходном диапазоне
            if self.top_point > self.max_v:
                self.top_point = self.max_v
            if self.low_point < self.min_v:
                self.low_point = self.min_v
            #следим, чтобы ширина не ушла в отрицательную величину
            if any([self.top_point == self.low_point, self.top_point < self.low_point]):
               return
            print("max - {}, min - {}".format(self.max_v, self.min_v))
            #корректируем срез
            self.temp_voxel[self.temp_voxel < self.low_point] = self.min_v
            self.temp_voxel[self.temp_voxel > self.top_point] = self.max_v
            imsave("temp.png", self.temp_voxel)
            self.background[self.current_slice] = cv2.imread("temp.png")
            back = self.background[self.current_slice].copy()
            img = cv2.add(back, self.current_mask)
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                
            image = QtGui.QImage(img, img.shape[1], img.shape[0],
                                          QtGui.QImage.Format_Grayscale8)
            transformed = image.convertToFormat(QtGui.QImage.Format_Grayscale8)
            self.pixmap = QtGui.QPixmap(transformed)
            self.label.setPixmap(self.pixmap)
            os.remove("temp.png")



