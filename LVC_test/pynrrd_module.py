from PyQt5 import QtWidgets
import nrrd
import cv2
import sys
from matplotlib.image import imsave
import numpy as np
import os
import form
import module_v
from PIL import Image, ImageOps, ImageEnhance
from PIL.ImageQt import ImageQt


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.ui = form.Ui_MainWindow()
        self.slices = None #массив обработанных слайсов
        self.initials = None #массив исходных слайсов
        self.percents = None #массив процентов поражения на слайсах
        self.voxels = None #массив исходных слайсов для использования в изменении уровня/ширины окна
        self.ui.setupUi(self)
        self.ui.estimate_button.clicked.connect(self.make_estimate)
        self.ui.exit_button.clicked.connect(self.close)
        self.ui.viz_button.clicked.connect(self.make_vizualization)
        self.ui.label.setFocus()

    def make_image_from_hu(self, hu):
        image = (np.maximum(hu, 0) / hu.max()) * 255.0
        image = np.uint8(image)
        return image

    def make_estimate(self):
        #загружаем массивы слайсов из nrrd-файлов
        file = nrrd.read('Segmentation-label.nrrd', index_order='C')
        initial = nrrd.read('2 Body 1.0.nrrd', index_order='C')
        initial = np.asarray(initial)[0]
        file = np.asarray(file)[0]
        fat_str = []
        outs = []
        back = []
        self.voxels = initial
        for i, img in enumerate(file):
            #приводим все исходные слайсы к легочному окну 
            #с уровнем -600 и шириной 1200 HU
            init_slice = initial[i]
            init_slice[init_slice < -1200] = np.amin(initial)
            init_slice[init_slice > 0] = np.amax(initial)

            print("init {}".format(i))
            image = self.make_image_from_hu(init_slice)
            back.append(image)

            print("slice {}".format(i))
            #img = img.astype(float)
            slice_ = self.make_image_from_hu(img)
            #делаем черными все пиксели не из зоны интереса (пиксель [0][0][0] черный)
            slice_[slice_ == slice_[0][0]] = 0
            #подсчитываем общую площадь области интереса
            place = np.count_nonzero(slice_)
            #делаем самые толстые структуры, выделенные яркими, белыми
            slice_[slice_ == slice_.max()] = 255
            #делаем все не белое черным
            slice_[slice_ != 255] = 0
            #создаем ядро 3х3 заполненное значением белого цвета
            kernel = np.full((3, 3), 255)
            #проводим по две итерации эрозии и дилатации
            out = cv2.erode(slice_, kernel, iterations=2)
            out = cv2.dilate(out, kernel, iterations=2)
            outs.append(out)
            #считаем процесс поражения через подсчёт числа оставшихся белых пикселей
            #на 3 делим так как у одного пикселя 3 значения (RGB)
            fat_structure = np.count_nonzero(out)
            #если на срезе вообще что-то есть
            if place != 0:
                fat_str.append(fat_structure / place)
            else: fat_str.append(0)
        self.percents = np.asarray(fat_str)
        self.slices = np.asarray(outs)
        self.initials = np.asarray(back)
        result = np.around(np.mean(self.percents) * 100, 2)
        self.ui.results.append("Percents is {}%".format(result))
       
    def make_vizualization(self):
        if any([self.initials is None, self.slices is None, self.percents is None]):
            QtWidgets.QMessageBox.critical(self, "Error",
                                           "Отсутствуют данные для выполнения визуализации!",
                                           defaultButton=QtWidgets.QMessageBox.Ok)
            return
        self.viz_window = module_v.Example(self.voxels, self.initials, self.slices, self.percents)
        self.viz_window.show()
        
app = QtWidgets.QApplication(sys.argv)
win = MainWindow()
win.show()
sys.exit(app.exec_())

    
