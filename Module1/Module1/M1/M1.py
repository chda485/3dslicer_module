import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import numpy as np
from PIL import Image
import time
import matplotlib.image as img_reader
import matplotlib.pyplot as plt
import cv2, sys, traceback
#
# M1
#

class M1(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "M1" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Examples"]
    self.parent.dependencies = []
    self.parent.contributors = ["John Doe (AnyWare Corp.)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
This is an example of scripted loadable module bundled in an extension.
It performs a simple thresholding on the input volume and optionally captures a screenshot.
"""
    self.parent.helpText += self.getDefaultModuleDocumentationLink()
    self.parent.acknowledgementText = """
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc.
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""" # replace with organization, grant and thanks.

#
# Window to vizualize results
#

class VizualizeWin(qt.QWidget):
    def __init__(self, background, slices, percents, parent=None):
        super().__init__(parent)
        self.background = background
        self.slices = slices
        self.percents = percents
        self.initUI()

    def initUI(self):
        self.slider = qt.QSlider(qt.Qt.Horizontal, self)
        #self.slider.setStyleSheet(SliderStyle)
        self.box = qt.QVBoxLayout()
        self.slider.setGeometry(120, 600, 290, 20)
        self.slider.setMinimum(0)
        self.box.addWidget(self.slider)
        self.slider.valueChanged.connect(self.changeValue)
        self.label = qt.QLabel(self)
        self.label.setGeometry(60, 40, 512, 512)
        self.box.addWidget(self.label)
        self.percent = qt.QLineEdit(self)
        self.percent.setGeometry(490, 600, 70, 20)
        self.percent.setEnabled(False)
        self.box.addWidget(self.percent)

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
        image = qt.QImage(img, img.shape[1], img.shape[0],
                                      qt.QImage.Format_RGB888)
        #transformed = image.convertToFormat(qt.QImage.Format_Grayscale8)
        self.pixmap = qt.QPixmap.fromImage(image)
        self.label.setPixmap(self.pixmap)

        self.percent.setText("%.2f %%" % (self.fat_s[0]))
        
        self.setLayout(self.box)
        self.setGeometry(300, 300, 300, 150)

    def changeValue(self, value):

        mask = self.images[value].copy()
        back = self.background[value].copy()
        img = cv2.add(back, mask)
        
        image = qt.QImage(img, img.shape[1], img.shape[0],
                                      qt.QImage.Format_RGB888)
        #transformed = image.convertToFormat(qt.QImage.Format_Grayscale8)
        self.pixmap = qt.QPixmap.fromImage(image)
        self.label.setPixmap(self.pixmap)

        self.percent.setText("%.2f %%" % (self.fat_s[value]))
        
#
# M1Widget
#

class M1Widget(ScriptedLoadableModuleWidget):
  """Uses ScriptedLoadableModuleWidget base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    visualization_choice = qt.QCheckBox("The visualization")
    parametersFormLayout.addWidget(visualization_choice)
    testButton = qt.QPushButton("Test the percent of fat structure")
    parametersFormLayout.addWidget(testButton)
    testButton.connect('clicked(bool)', self.onButtonClicked)

    self.layout.addStretch(5)

    self.testButton = testButton
    self.visualization_choice = visualization_choice

  def onButtonClicked(self):
    logic = M1Logic()
    visualization = self.visualization_choice.isChecked()
    """часть кода отвечающая за визуализацию результатов"""
    if visualization:
        try:
            (back, slices, fat_s) = logic.process(visualization)
            app = qt.QApplication
            window = VizualizeWin(back, slices, fat_s)
            window.show()
            try:
                sys.exit(app.exec_())
            except:
                print("error")
        except:
            (type_e, value, trace) = sys.exc_info()
            print(sys.excepthook(type_e, value, trace))
    else:
        result = logic.process()
        qt.QMessageBox.information(slicer.util.mainWindow(), 'Fat structure', result)

# M1Logic
#

class M1Logic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget.
  Uses ScriptedLoadableModuleLogic base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def erosion(self, slice_img):
      H, W = slice_img.shape
      filter = np.array(((0,0,0),
   			           (0,0,0),
   			           (0,0,0)), dtype=np.int)
      out_slice = slice_img.copy()
      tmp = np.pad(slice_img, (1,1), 'edge')
      for i in range(1, H):
   		  for j in range(1, W):
   			  if np.array_equal(filter, tmp[i-1:i+2, j-1: j+2]):
   				  out_slice[i,j] = 0
   			  else: out_slice[i,j] = 1
    
      return out_slice

  """function dilate make the pixel zero if at least one pixel
  surround center equal zero
  """

  def dilate(self, slice_img):
      H, W = slice_img.shape
      out_slice = slice_img.copy()
      tmp = np.pad(slice_img, (1,1), 'edge')
      for i in range(1, H):
          for j in range(1, W):
              if np.sum(tmp[i-1:i+2, j-1: j+2]) < 9:
                  out_slice[i,j] = 0
              else: out_slice[i,j] = 1
      return out_slice

  def show_vizualization(self, initial, out):
      img_reader.imsave('initial.png', initial)
      img_reader.imsave('slice.png', out)
      mask = Image.open('slice.png')
      mask = mask.convert("L")
      result = Image.open('initial.png')
      Image.Image.paste(result, mask, mask=mask)
      result.save('result.png')
      result = Image.open('result.png')
      result.show()
      os.remove('initial.png')
      os.remove('slice.png')
      os.remove('result.png')

  
  def process(self, visualization=False):
        startT = time.time()
        array = slicer.util.array('Segmentation-label')
        initial = slicer.util.array('2 Body 1.0')
        fat_str = []
        images = []
        initials = []
        for i in range(array.shape[0]):
          img_reader.imsave('slice.png', array[i])
          img_reader.imsave('initial.png', initial[i])
          
          slice_img = cv2.imread('slice.png')
          initial_img = cv2.imread('initial.png')
          initials.append(initial_img)
          
          """делаем все пиксели фона черными"""
          slice_img[slice_img[:,:,0] == slice_img[0][0][0]] = 0
          place = np.count_nonzero(slice_img) // 3
          """делаем самые толстые структуры, выделенные яркими, белыми"""
          slice_img[slice_img[:,:,1] == slice_img[:,:,1].max()] = 255
          """делаем все не белое черным"""
          slice_img[slice_img[:,:,0:3] != 255] = 0
          kernel = np.full((3, 3), 255)
          out = cv2.erode(slice_img, kernel, iterations=1)
          out = cv2.dilate(out, kernel, iterations=1)
          images.append(out)
          fat_structure = np.count_nonzero(out) // 3
          if place != 0:
            fat_str.append(fat_structure / place)
          else: fat_str.append(0)
        os.remove('slice.png')
        os.remove('initial.png')
        fat_str = np.asarray(fat_str)
        itcome = np.mean(fat_str) * 100
        endT = time.time()
        resultT = endT - startT
        if visualization:
          return (np.asarray(initials), np.asarray(images), fat_str)
        else:
          return "Fat structure is {} %. Time is {} sec".format(
              np.around(itcome,2), np.around(resultT,2))
  
class M1Test(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_M11()

  def test_M11(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting Test")
    logic = M1Logic()
    result = logic.process()
    self.delayDisplay(result)
    self.assertIsNotNone(result)
    self.delayDisplay('Test passed!')
