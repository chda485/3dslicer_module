from PyQt5 import QtWidgets
import nrrd, cv2, sys
import matplotlib.image as img_reader
import numpy as np
import os, form, module_v


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        self.ui = form.Ui_MainWindow()
        self.slices = None
        self.initials = None
        self.percents = None
        self.ui.setupUi(self)
        self.ui.estimate_button.clicked.connect(self.make_estimate)
        self.ui.exit_button.clicked.connect(self.close)
        self.ui.viz_button.clicked.connect(self.make_vizualization)
        self.ui.label.setFocus()
        
    def make_estimate(self):
        file = nrrd.read('Segmentation-label.nrrd', index_order='C')
        initial = nrrd.read('2 Body 1.0.nrrd', index_order='C')
        initial = np.asarray(initial)[0]
        file = np.asarray(file)[0]
        fat_str = []
        outs = []
        back = []
        for i, img in enumerate(file):
            img_reader.imsave('slice.png', img)
            img_reader.imsave('initial.png', initial[i])
            slice_ = cv2.imread('slice.png')
            image = cv2.imread('initial.png')
            back.append(image)
            
            slice_[slice_[:,:,0] == slice_[0][0][0]] = 0
            place = np.count_nonzero(slice_) // 3
            #делаем самые толстые структуры, выделенные яркими, белыми
            slice_[slice_[:,:,1] == slice_[:,:,1].max()] = 255
            #делаем все не белое черным
            slice_[slice_[:,:,0:3] != 255] = 0
            
            kernel = np.full((3, 3), 255)
            out = slice_
            out = cv2.erode(out, kernel, iterations=2)
            out = cv2.dilate(out, kernel, iterations=2)
            outs.append(out)
            fat_structure = np.count_nonzero(out) // 3
            if place != 0:
                fat_str.append(fat_structure / place)
            else: fat_str.append(0)
        self.percents = np.asarray(fat_str)
        self.slices = np.asarray(outs)
        self.initials = np.asarray(back)
        result = np.around(np.mean(self.percents) * 100, 2)
        self.ui.results.append("Percents is {}%".format(result))
        os.remove('slice.png')
        os.remove('initial.png')
       
    def make_vizualization(self):
        if self.initials is None or self.slices is None or self.percents is None:
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

    
