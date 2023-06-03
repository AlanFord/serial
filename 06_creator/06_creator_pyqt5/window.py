# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'window.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(800, 600)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.button1 = QtWidgets.QPushButton(Form)
        self.button1.setObjectName("button1")
        self.verticalLayout.addWidget(self.button1)
        self.button2 = QtWidgets.QPushButton(Form)
        self.button2.setObjectName("button2")
        self.verticalLayout.addWidget(self.button2)
        self.button3 = QtWidgets.QPushButton(Form)
        self.button3.setObjectName("button3")
        self.verticalLayout.addWidget(self.button3)
        self.plot = GraphWidget(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.plot.sizePolicy().hasHeightForWidth())
        self.plot.setSizePolicy(sizePolicy)
        self.plot.setObjectName("plot")
        self.verticalLayout.addWidget(self.plot)

        self.retranslateUi(Form)
        self.button1.clicked.connect(self.plot.repaint)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Graphing Thing!"))
        self.button1.setText(_translate("Form", "START"))
        self.button2.setText(_translate("Form", "STOP"))
        self.button3.setText(_translate("Form", "Done"))
from graph_widget import GraphWidget
