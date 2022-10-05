# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'mainWindowicTywg.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(395, 265)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setAutoFillBackground(False)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        sizePolicy1 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.centralwidget.sizePolicy().hasHeightForWidth())
        self.centralwidget.setSizePolicy(sizePolicy1)
        self.centralwidget.setAutoFillBackground(True)
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox_inputs = QGroupBox(self.centralwidget)
        self.groupBox_inputs.setObjectName(u"groupBox_inputs")
        self.formLayout_2 = QFormLayout(self.groupBox_inputs)
        self.formLayout_2.setObjectName(u"formLayout_2")
        self.btn_SelectFolder = QPushButton(self.groupBox_inputs)
        self.btn_SelectFolder.setObjectName(u"btn_SelectFolder")

        self.formLayout_2.setWidget(0, QFormLayout.LabelRole, self.btn_SelectFolder)

        self.input_folder = QLineEdit(self.groupBox_inputs)
        self.input_folder.setObjectName(u"input_folder")

        self.formLayout_2.setWidget(0, QFormLayout.FieldRole, self.input_folder)


        self.verticalLayout.addWidget(self.groupBox_inputs)

        self.groupBox_options = QGroupBox(self.centralwidget)
        self.groupBox_options.setObjectName(u"groupBox_options")
        self.groupBox_options.setMinimumSize(QSize(300, 50))
        self.groupBox_options.setBaseSize(QSize(0, 0))
        self.gridLayout_2 = QGridLayout(self.groupBox_options)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.formLayout_3 = QFormLayout()
        self.formLayout_3.setObjectName(u"formLayout_3")
        self.chk_resizeImg = QCheckBox(self.groupBox_options)
        self.chk_resizeImg.setObjectName(u"chk_resizeImg")

        self.formLayout_3.setWidget(1, QFormLayout.LabelRole, self.chk_resizeImg)

        self.cmb_resizeImg = QComboBox(self.groupBox_options)
        self.cmb_resizeImg.addItem("")
        self.cmb_resizeImg.addItem("")
        self.cmb_resizeImg.addItem("")
        self.cmb_resizeImg.addItem("")
        self.cmb_resizeImg.addItem("")
        self.cmb_resizeImg.addItem("")
        self.cmb_resizeImg.setObjectName(u"cmb_resizeImg")

        self.formLayout_3.setWidget(1, QFormLayout.FieldRole, self.cmb_resizeImg)

        self.chk_restoreBackups = QCheckBox(self.groupBox_options)
        self.chk_restoreBackups.setObjectName(u"chk_restoreBackups")
        self.chk_restoreBackups.setEnabled(True)
        self.chk_restoreBackups.setAutoFillBackground(False)
        self.chk_restoreBackups.setChecked(True)
        self.chk_restoreBackups.setAutoRepeat(True)

        self.formLayout_3.setWidget(0, QFormLayout.LabelRole, self.chk_restoreBackups)


        self.horizontalLayout.addLayout(self.formLayout_3)

        self.line = QFrame(self.groupBox_options)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.VLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.horizontalLayout.addWidget(self.line)

        self.formLayout_4 = QFormLayout()
        self.formLayout_4.setObjectName(u"formLayout_4")
        self.formLayout_4.setFormAlignment(Qt.AlignLeading|Qt.AlignLeft|Qt.AlignTop)
        self.chk_recursive = QCheckBox(self.groupBox_options)
        self.chk_recursive.setObjectName(u"chk_recursive")
        self.chk_recursive.setLayoutDirection(Qt.LeftToRight)
        self.chk_recursive.setAutoFillBackground(False)

        self.formLayout_4.setWidget(0, QFormLayout.FieldRole, self.chk_recursive)


        self.horizontalLayout.addLayout(self.formLayout_4)


        self.gridLayout_2.addLayout(self.horizontalLayout, 0, 0, 1, 1)


        self.verticalLayout.addWidget(self.groupBox_options)

        self.groupBox_actions = QGroupBox(self.centralwidget)
        self.groupBox_actions.setObjectName(u"groupBox_actions")
        self.formLayout = QFormLayout(self.groupBox_actions)
        self.formLayout.setObjectName(u"formLayout")
        self.btn_Optimize = QPushButton(self.groupBox_actions)
        self.btn_Optimize.setObjectName(u"btn_Optimize")

        self.formLayout.setWidget(0, QFormLayout.SpanningRole, self.btn_Optimize)


        self.verticalLayout.addWidget(self.groupBox_actions)


        self.gridLayout.addLayout(self.verticalLayout, 1, 0, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 395, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.cmb_resizeImg.setCurrentIndex(4)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.groupBox_inputs.setTitle(QCoreApplication.translate("MainWindow", u"Input", None))
        self.btn_SelectFolder.setText(QCoreApplication.translate("MainWindow", u"Select Folder", None))
        self.input_folder.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Select a Folder to Convert", None))
        self.groupBox_options.setTitle(QCoreApplication.translate("MainWindow", u"Options", None))
#if QT_CONFIG(tooltip)
        self.chk_resizeImg.setToolTip(QCoreApplication.translate("MainWindow", u"Every Image bigger than the selected resolution will be downscaled to that Resolution", None))
#endif // QT_CONFIG(tooltip)
        self.chk_resizeImg.setText(QCoreApplication.translate("MainWindow", u"Resize Images", None))
        self.cmb_resizeImg.setItemText(0, QCoreApplication.translate("MainWindow", u"128", None))
        self.cmb_resizeImg.setItemText(1, QCoreApplication.translate("MainWindow", u"256", None))
        self.cmb_resizeImg.setItemText(2, QCoreApplication.translate("MainWindow", u"512", None))
        self.cmb_resizeImg.setItemText(3, QCoreApplication.translate("MainWindow", u"1024", None))
        self.cmb_resizeImg.setItemText(4, QCoreApplication.translate("MainWindow", u"2048", None))
        self.cmb_resizeImg.setItemText(5, QCoreApplication.translate("MainWindow", u"4096", None))

#if QT_CONFIG(tooltip)
        self.cmb_resizeImg.setToolTip(QCoreApplication.translate("MainWindow", u"Resize images to this Resolution.\n"
"Only images that are BIGGER Than the selected resolution will be resized", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.cmb_resizeImg.setStatusTip("")
#endif // QT_CONFIG(statustip)
#if QT_CONFIG(tooltip)
        self.chk_restoreBackups.setToolTip(QCoreApplication.translate("MainWindow", u"On: RestoreBackupFiles and optimize those files\n"
"Off: Use existing Var Files and optimize those", None))
#endif // QT_CONFIG(tooltip)
        self.chk_restoreBackups.setText(QCoreApplication.translate("MainWindow", u"Retore Backups", None))
#if QT_CONFIG(tooltip)
        self.chk_recursive.setToolTip(QCoreApplication.translate("MainWindow", u"Also Optimise Subfolders", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.chk_recursive.setStatusTip("")
#endif // QT_CONFIG(statustip)
#if QT_CONFIG(whatsthis)
        self.chk_recursive.setWhatsThis("")
#endif // QT_CONFIG(whatsthis)
        self.chk_recursive.setText(QCoreApplication.translate("MainWindow", u"Recursive (Subfolders)", None))
        self.groupBox_actions.setTitle(QCoreApplication.translate("MainWindow", u"Actions", None))
        self.btn_Optimize.setText(QCoreApplication.translate("MainWindow", u"Optimze !", None))
    # retranslateUi
