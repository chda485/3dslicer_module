from PyQt5 import QtWidgets

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):

        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding, QtWidgets.QSizePolicy.Fixed)
        self.label = QtWidgets.QLabel('Оценка поражения легочной ткани при COVID-19')
        self.results = QtWidgets.QLineEdit()
        self.estimate_button = QtWidgets.QPushButton('Произвести\nоценку')
        self.viz_button = QtWidgets.QPushButton('Визуализировать\nрезультаты')
        self.exit_button = QtWidgets.QPushButton('Выход')

        self.base_layout = QtWidgets.QVBoxLayout()
        self.buttons_layout = QtWidgets.QHBoxLayout()
        self.buttons_layout.setContentsMargins(0, 0, 0, 0)
        self.buttons_layout.addWidget(self.estimate_button)
        self.buttons_layout.addWidget(self.viz_button)
        self.exit_layout = QtWidgets.QHBoxLayout()
        self.exit_layout.setContentsMargins(0, 0, 0, 0)
        self.exit_layout.addStretch()
        self.exit_layout.addWidget(self.exit_button)
        self.base_layout.addLayout(self.buttons_layout)
        self.base_layout.addWidget(self.results)
        self.base_layout.addLayout(self.exit_layout)

        self.centralwidget.setLayout(self.base_layout)
        MainWindow.setFixedWidth(350)
        MainWindow.setFixedHeight(150)
        MainWindow.setCentralWidget(self.centralwidget)

