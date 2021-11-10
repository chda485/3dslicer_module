from PyQt5 import QtWidgets
import nrrd
import cv2
import sys
import numpy as np
import form
import module_v
import pydicom as pyd
import os

PATH_TO_DICOM = r"E:\projects\python\dicom\materials\CODES\LVC_test_scans (1)\03_08_2020_12_10_09"

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.ui = form.Ui_MainWindow()
        self.slices = None #массив обработанных слайсов
        self.initials = None #массив исходных слайсов
        self.percents = None #массив процентов поражения на слайсах
        self.ui.setupUi(self)
        self.ui.estimate_button.clicked.connect(self.make_estimate)
        self.ui.exit_button.clicked.connect(self.close)
        self.ui.viz_button.clicked.connect(self.make_vizualization)
        self.ui.label.setFocus()

    def make_image_from_hu(self, hu):
        image = (np.maximum(hu, 0) / hu.max()) * 255.0
        #преобразуем к uint8 так как ImageEnhance требует это для изменения яркости/контраста
        image = np.uint8(image)
        return image

    def make_array_from_dicom(self, path):
        images = os.listdir(path)
        imgs = []
        for image in images:
            imgP = os.path.join(path, image)
            img = pyd.read_file(imgP)
            img = img.pixel_array.astype('float')
            imgs.append(img)
        return np.asarray(imgs)

    def make_estimate(self):
        #загружаем массивы слайсов из nrrd-файлов
        file = nrrd.read('Segmentation-label.nrrd', index_order='C')
        #создаем массив изображений их dicom-исходника
        initial = self.make_array_from_dicom(PATH_TO_DICOM)
        #initial = np.asarray(initial)[0]
        file = np.asarray(file)[0]
        fat_str = []
        outs = []
        back = []
        min_ = np.amin(initial)
        max_ = np.amax(initial)
        for i, img in enumerate(file):
            #приводим все исходные слайсы к легочному окну 
            #с уровнем -600 и шириной 1200 HU
            init_slice = initial[i]
            #init_slice[init_slice < -1200] = min_
            #init_slice[init_slice > 0] = max_
            print("init {}".format(i))
            #создаём картинку из исходного слайса
            image = self.make_image_from_hu(init_slice)

            print("slice {}".format(i))
            #создаём картинку из массива HU
            slice_ = self.make_image_from_hu(img)
            #подсчитываем общую площадь области интереса
            place = np.count_nonzero(slice_)
            #создаем ядро 3х3 заполненное значением белого цвета
            kernel = np.full((3, 3), 255)
            #проводим по две итерации эрозии и дилатации
            out = cv2.erode(slice_, kernel, iterations=2)
            out = cv2.dilate(out, kernel, iterations=2)
            #оставляем только толстые структуры
            #(на выходе дилатации массив с тремя вариантами значений:
            #0 - фон картинки, 127 - общая картинка легких,
            #255 - предполагаемые толстые структуры)
            out[out != 255] = 0
            #считаем процесс поражения через подсчёт числа оставшихся белых пикселей
            fat_structure = np.count_nonzero(out)
            #если на срезе вообще что-то есть
            if place != 0 and fat_structure != 0:
                fat_str.append(fat_structure / place)
                back.append(image)
                outs.append(out)
            else:
                continue
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
        self.viz_window = module_v.Example(self.initials, self.slices, self.percents)
        self.viz_window.show()
        
app = QtWidgets.QApplication(sys.argv)
win = MainWindow()
win.show()
sys.exit(app.exec_())

    
