# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'octron.ui'
##
## Created by: Qt User Interface Compiler version 5.15.16
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide2.QtCore import *  # type: ignore
from PySide2.QtGui import *  # type: ignore
from PySide2.QtWidgets import *  # type: ignore


class Ui_octron_widgetui(object):
    def setupUi(self, octron_widgetui):
        if not octron_widgetui.objectName():
            octron_widgetui.setObjectName(u"octron_widgetui")
        octron_widgetui.setEnabled(True)
        octron_widgetui.resize(410, 700)
        octron_widgetui.setMinimumSize(QSize(410, 700))
        octron_widgetui.setMaximumSize(QSize(410, 800))
        octron_widgetui.setCursor(QCursor(Qt.ArrowCursor))
        octron_widgetui.setWindowOpacity(1.000000000000000)
        self.verticalLayoutWidget = QWidget(octron_widgetui)
        self.verticalLayoutWidget.setObjectName(u"verticalLayoutWidget")
        self.verticalLayoutWidget.setGeometry(QRect(0, 0, 412, 651))
        self.mainLayout = QVBoxLayout(self.verticalLayoutWidget)
        self.mainLayout.setSpacing(10)
        self.mainLayout.setObjectName(u"mainLayout")
        self.mainLayout.setSizeConstraint(QLayout.SizeConstraint.SetNoConstraint)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.octron_logo = QLabel(self.verticalLayoutWidget)
        self.octron_logo.setObjectName(u"octron_logo")
        self.octron_logo.setEnabled(True)
        self.octron_logo.setMinimumSize(QSize(410, 100))
        self.octron_logo.setBaseSize(QSize(0, 0))
        self.octron_logo.setLineWidth(0)
        self.octron_logo.setPixmap(QPixmap(u"octron_logo.svg"))
        self.octron_logo.setAlignment(Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop)

        self.mainLayout.addWidget(self.octron_logo, 0, Qt.AlignmentFlag.AlignLeft)

        self.toolBox = QToolBox(self.verticalLayoutWidget)
        self.toolBox.setObjectName(u"toolBox")
        self.toolBox.setEnabled(True)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.toolBox.sizePolicy().hasHeightForWidth())
        self.toolBox.setSizePolicy(sizePolicy)
        self.toolBox.setMinimumSize(QSize(0, 0))
        self.toolBox.setMaximumSize(QSize(410, 750))
        self.toolBox.setCursor(QCursor(Qt.ArrowCursor))
        self.toolBox.setFrameShape(QFrame.Shape.NoFrame)
        self.toolBox.setFrameShadow(QFrame.Shadow.Plain)
        self.toolBox.setLineWidth(0)
        self.toolBox.setMidLineWidth(0)
        self.project_tab = QWidget()
        self.project_tab.setObjectName(u"project_tab")
        self.project_tab.setGeometry(QRect(0, 0, 410, 387))
        sizePolicy1 = QSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.project_tab.sizePolicy().hasHeightForWidth())
        self.project_tab.setSizePolicy(sizePolicy1)
        icon = QIcon()
        icon.addFile(u"icons/noun-project-7158867.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolBox.addItem(self.project_tab, icon, u"Project")
        self.annotate_tab = QWidget()
        self.annotate_tab.setObjectName(u"annotate_tab")
        self.annotate_tab.setGeometry(QRect(0, 0, 405, 387))
        sizePolicy1.setHeightForWidth(self.annotate_tab.sizePolicy().hasHeightForWidth())
        self.annotate_tab.setSizePolicy(sizePolicy1)
        self.annotate_tab.setMaximumSize(QSize(405, 700))
        self.verticalLayoutWidget_2 = QWidget(self.annotate_tab)
        self.verticalLayoutWidget_2.setObjectName(u"verticalLayoutWidget_2")
        self.verticalLayoutWidget_2.setGeometry(QRect(0, 0, 402, 391))
        self.annotate_vertical_layout = QVBoxLayout(self.verticalLayoutWidget_2)
#ifndef Q_OS_MAC
        self.annotate_vertical_layout.setSpacing(-1)
#endif
        self.annotate_vertical_layout.setObjectName(u"annotate_vertical_layout")
        self.annotate_vertical_layout.setContentsMargins(0, 0, 0, 10)
        self.horizontalGroupBox = QGroupBox(self.verticalLayoutWidget_2)
        self.horizontalGroupBox.setObjectName(u"horizontalGroupBox")
        sizePolicy2 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.horizontalGroupBox.sizePolicy().hasHeightForWidth())
        self.horizontalGroupBox.setSizePolicy(sizePolicy2)
        self.horizontalGroupBox.setMinimumSize(QSize(400, 60))
        self.horizontalGroupBox.setMaximumSize(QSize(400, 60))
        self.horizontalLayout_8 = QHBoxLayout(self.horizontalGroupBox)
        self.horizontalLayout_8.setSpacing(20)
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(9, 9, 9, 9)
        self.sam2model_list = QComboBox(self.horizontalGroupBox)
        self.sam2model_list.addItem("")
        self.sam2model_list.setObjectName(u"sam2model_list")
        self.sam2model_list.setMinimumSize(QSize(167, 25))
        self.sam2model_list.setMaximumSize(QSize(167, 25))

        self.horizontalLayout_8.addWidget(self.sam2model_list, 0, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.load_model_btn = QPushButton(self.horizontalGroupBox)
        self.load_model_btn.setObjectName(u"load_model_btn")
        self.load_model_btn.setMinimumSize(QSize(0, 25))
        self.load_model_btn.setMaximumSize(QSize(250, 25))

        self.horizontalLayout_8.addWidget(self.load_model_btn, 0, Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)


        self.annotate_vertical_layout.addWidget(self.horizontalGroupBox, 0, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop)

        self.annotate_layer_create_groupbox = QGroupBox(self.verticalLayoutWidget_2)
        self.annotate_layer_create_groupbox.setObjectName(u"annotate_layer_create_groupbox")
        sizePolicy2.setHeightForWidth(self.annotate_layer_create_groupbox.sizePolicy().hasHeightForWidth())
        self.annotate_layer_create_groupbox.setSizePolicy(sizePolicy2)
        self.annotate_layer_create_groupbox.setMinimumSize(QSize(400, 90))
        self.annotate_layer_create_groupbox.setMaximumSize(QSize(400, 90))
        self.gridLayout = QGridLayout(self.annotate_layer_create_groupbox)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setSizeConstraint(QLayout.SizeConstraint.SetDefaultConstraint)
        self.gridLayout.setHorizontalSpacing(20)
        self.gridLayout.setVerticalSpacing(9)
        self.gridLayout.setContentsMargins(9, 9, 9, 9)
        self.label_list_combobox = QComboBox(self.annotate_layer_create_groupbox)
        self.label_list_combobox.addItem("")
        self.label_list_combobox.addItem("")
        self.label_list_combobox.addItem("")
        self.label_list_combobox.setObjectName(u"label_list_combobox")
        self.label_list_combobox.setMinimumSize(QSize(110, 25))
        self.label_list_combobox.setMaximumSize(QSize(110, 25))
        self.label_list_combobox.setEditable(False)
        self.label_list_combobox.setMaxCount(15)
        self.label_list_combobox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.label_list_combobox.setIconSize(QSize(14, 14))
        self.label_list_combobox.setFrame(False)

        self.gridLayout.addWidget(self.label_list_combobox, 0, 2, 1, 1, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.layer_type_combobox = QComboBox(self.annotate_layer_create_groupbox)
        self.layer_type_combobox.addItem("")
        self.layer_type_combobox.addItem("")
        self.layer_type_combobox.addItem("")
        self.layer_type_combobox.addItem("")
        self.layer_type_combobox.setObjectName(u"layer_type_combobox")
        self.layer_type_combobox.setMinimumSize(QSize(110, 25))
        self.layer_type_combobox.setMaximumSize(QSize(110, 25))
        self.layer_type_combobox.setMaxCount(15)
        self.layer_type_combobox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
        self.layer_type_combobox.setIconSize(QSize(14, 14))
        self.layer_type_combobox.setFrame(False)

        self.gridLayout.addWidget(self.layer_type_combobox, 0, 0, 1, 1, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.create_annotation_layer_btn = QPushButton(self.annotate_layer_create_groupbox)
        self.create_annotation_layer_btn.setObjectName(u"create_annotation_layer_btn")
        self.create_annotation_layer_btn.setMinimumSize(QSize(70, 25))
        self.create_annotation_layer_btn.setMaximumSize(QSize(70, 25))

        self.gridLayout.addWidget(self.create_annotation_layer_btn, 0, 4, 1, 1, Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)

        self.label_suffix_lineedit = QLineEdit(self.annotate_layer_create_groupbox)
        self.label_suffix_lineedit.setObjectName(u"label_suffix_lineedit")
        self.label_suffix_lineedit.setMinimumSize(QSize(60, 25))
        self.label_suffix_lineedit.setMaximumSize(QSize(60, 25))
        self.label_suffix_lineedit.setInputMask(u"")
        self.label_suffix_lineedit.setText(u"")
        self.label_suffix_lineedit.setMaxLength(100)

        self.gridLayout.addWidget(self.label_suffix_lineedit, 0, 3, 1, 1, Qt.AlignmentFlag.AlignVCenter)

        self.hard_reset_layer_btn = QPushButton(self.annotate_layer_create_groupbox)
        self.hard_reset_layer_btn.setObjectName(u"hard_reset_layer_btn")
        self.hard_reset_layer_btn.setMinimumSize(QSize(70, 25))
        self.hard_reset_layer_btn.setMaximumSize(QSize(70, 25))
        self.hard_reset_layer_btn.setAutoRepeatInterval(2000)

        self.gridLayout.addWidget(self.hard_reset_layer_btn, 1, 4, 1, 1, Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)

        self.create_projection_layer_btn = QPushButton(self.annotate_layer_create_groupbox)
        self.create_projection_layer_btn.setObjectName(u"create_projection_layer_btn")
        self.create_projection_layer_btn.setMinimumSize(QSize(110, 25))
        self.create_projection_layer_btn.setMaximumSize(QSize(110, 25))

        self.gridLayout.addWidget(self.create_projection_layer_btn, 1, 0, 1, 1, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)


        self.annotate_vertical_layout.addWidget(self.annotate_layer_create_groupbox, 0, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignTop)

        self.annotate_param_groupbox = QGroupBox(self.verticalLayoutWidget_2)
        self.annotate_param_groupbox.setObjectName(u"annotate_param_groupbox")
        sizePolicy3 = QSizePolicy(QSizePolicy.Maximum, QSizePolicy.Maximum)
        sizePolicy3.setHorizontalStretch(100)
        sizePolicy3.setVerticalStretch(0)
        sizePolicy3.setHeightForWidth(self.annotate_param_groupbox.sizePolicy().hasHeightForWidth())
        self.annotate_param_groupbox.setSizePolicy(sizePolicy3)
        self.annotate_param_groupbox.setMinimumSize(QSize(400, 60))
        self.annotate_param_groupbox.setMaximumSize(QSize(400, 60))
        self.horizontalLayout_4 = QHBoxLayout(self.annotate_param_groupbox)
        self.horizontalLayout_4.setSpacing(20)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.horizontalLayout_4.setContentsMargins(9, 9, 9, 9)
        self.kernel_label = QLabel(self.annotate_param_groupbox)
        self.kernel_label.setObjectName(u"kernel_label")
        sizePolicy4 = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        sizePolicy4.setHorizontalStretch(0)
        sizePolicy4.setVerticalStretch(0)
        sizePolicy4.setHeightForWidth(self.kernel_label.sizePolicy().hasHeightForWidth())
        self.kernel_label.setSizePolicy(sizePolicy4)
        self.kernel_label.setMaximumSize(QSize(400, 25))

        self.horizontalLayout_4.addWidget(self.kernel_label, 0, Qt.AlignmentFlag.AlignLeft|Qt.AlignmentFlag.AlignVCenter)

        self.opening_kernel_radius_input = QSpinBox(self.annotate_param_groupbox)
        self.opening_kernel_radius_input.setObjectName(u"opening_kernel_radius_input")
        sizePolicy5 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy5.setHorizontalStretch(0)
        sizePolicy5.setVerticalStretch(0)
        sizePolicy5.setHeightForWidth(self.opening_kernel_radius_input.sizePolicy().hasHeightForWidth())
        self.opening_kernel_radius_input.setSizePolicy(sizePolicy5)
        self.opening_kernel_radius_input.setMinimumSize(QSize(60, 25))
        self.opening_kernel_radius_input.setMaximumSize(QSize(60, 25))
        self.opening_kernel_radius_input.setAlignment(Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignTrailing|Qt.AlignmentFlag.AlignVCenter)
        self.opening_kernel_radius_input.setButtonSymbols(QAbstractSpinBox.ButtonSymbols.PlusMinus)
        self.opening_kernel_radius_input.setMaximum(20)
        self.opening_kernel_radius_input.setValue(5)

        self.horizontalLayout_4.addWidget(self.opening_kernel_radius_input, 0, Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)


        self.annotate_vertical_layout.addWidget(self.annotate_param_groupbox, 0, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignBottom)

        self.annotate_layer_predict_groupbox = QGroupBox(self.verticalLayoutWidget_2)
        self.annotate_layer_predict_groupbox.setObjectName(u"annotate_layer_predict_groupbox")
        sizePolicy2.setHeightForWidth(self.annotate_layer_predict_groupbox.sizePolicy().hasHeightForWidth())
        self.annotate_layer_predict_groupbox.setSizePolicy(sizePolicy2)
        self.annotate_layer_predict_groupbox.setMinimumSize(QSize(400, 60))
        self.annotate_layer_predict_groupbox.setMaximumSize(QSize(400, 60))
        self.horizontalLayout_7 = QHBoxLayout(self.annotate_layer_predict_groupbox)
        self.horizontalLayout_7.setSpacing(20)
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.horizontalLayout_7.setContentsMargins(9, 9, 9, 9)
        self.batch_predict_progressbar = QProgressBar(self.annotate_layer_predict_groupbox)
        self.batch_predict_progressbar.setObjectName(u"batch_predict_progressbar")
        sizePolicy6 = QSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.Fixed)
        sizePolicy6.setHorizontalStretch(0)
        sizePolicy6.setVerticalStretch(0)
        sizePolicy6.setHeightForWidth(self.batch_predict_progressbar.sizePolicy().hasHeightForWidth())
        self.batch_predict_progressbar.setSizePolicy(sizePolicy6)
        self.batch_predict_progressbar.setMinimumSize(QSize(200, 25))
        self.batch_predict_progressbar.setMaximumSize(QSize(255, 25))
        self.batch_predict_progressbar.setMaximum(20)
        self.batch_predict_progressbar.setValue(0)

        self.horizontalLayout_7.addWidget(self.batch_predict_progressbar)

        self.predict_next_batch_btn = QPushButton(self.annotate_layer_predict_groupbox)
        self.predict_next_batch_btn.setObjectName(u"predict_next_batch_btn")
        self.predict_next_batch_btn.setEnabled(False)
        self.predict_next_batch_btn.setMinimumSize(QSize(0, 25))
        self.predict_next_batch_btn.setMaximumSize(QSize(250, 25))

        self.horizontalLayout_7.addWidget(self.predict_next_batch_btn, 0, Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)


        self.annotate_vertical_layout.addWidget(self.annotate_layer_predict_groupbox, 0, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignBottom)

        self.annotate_layer_save_groupbox = QGroupBox(self.verticalLayoutWidget_2)
        self.annotate_layer_save_groupbox.setObjectName(u"annotate_layer_save_groupbox")
        sizePolicy2.setHeightForWidth(self.annotate_layer_save_groupbox.sizePolicy().hasHeightForWidth())
        self.annotate_layer_save_groupbox.setSizePolicy(sizePolicy2)
        self.annotate_layer_save_groupbox.setMinimumSize(QSize(400, 60))
        self.annotate_layer_save_groupbox.setMaximumSize(QSize(400, 60))
        self.horizontalLayout_9 = QHBoxLayout(self.annotate_layer_save_groupbox)
        self.horizontalLayout_9.setSpacing(20)
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(9, 9, 9, 9)
        self.batch_save_progressbar = QProgressBar(self.annotate_layer_save_groupbox)
        self.batch_save_progressbar.setObjectName(u"batch_save_progressbar")
        self.batch_save_progressbar.setEnabled(False)
        sizePolicy6.setHeightForWidth(self.batch_save_progressbar.sizePolicy().hasHeightForWidth())
        self.batch_save_progressbar.setSizePolicy(sizePolicy6)
        self.batch_save_progressbar.setMinimumSize(QSize(200, 25))
        self.batch_save_progressbar.setMaximumSize(QSize(255, 25))
        self.batch_save_progressbar.setMaximum(20)
        self.batch_save_progressbar.setValue(0)

        self.horizontalLayout_9.addWidget(self.batch_save_progressbar)

        self.export_annotations_label = QLabel(self.annotate_layer_save_groupbox)
        self.export_annotations_label.setObjectName(u"export_annotations_label")
        self.export_annotations_label.setEnabled(False)

        self.horizontalLayout_9.addWidget(self.export_annotations_label, 0, Qt.AlignmentFlag.AlignVCenter)

        self.export_annotations_btn = QPushButton(self.annotate_layer_save_groupbox)
        self.export_annotations_btn.setObjectName(u"export_annotations_btn")
        self.export_annotations_btn.setEnabled(False)
        self.export_annotations_btn.setMinimumSize(QSize(0, 25))
        self.export_annotations_btn.setMaximumSize(QSize(250, 25))

        self.horizontalLayout_9.addWidget(self.export_annotations_btn, 0, Qt.AlignmentFlag.AlignRight|Qt.AlignmentFlag.AlignVCenter)


        self.annotate_vertical_layout.addWidget(self.annotate_layer_save_groupbox, 0, Qt.AlignmentFlag.AlignHCenter|Qt.AlignmentFlag.AlignBottom)

        icon1 = QIcon()
        icon1.addFile(u"icons/noun-copywriting-7158879.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolBox.addItem(self.annotate_tab, icon1, u"Generate training data (annotate)")
        self.train_tab = QWidget()
        self.train_tab.setObjectName(u"train_tab")
        self.train_tab.setGeometry(QRect(0, 0, 410, 387))
        sizePolicy1.setHeightForWidth(self.train_tab.sizePolicy().hasHeightForWidth())
        self.train_tab.setSizePolicy(sizePolicy1)
        icon2 = QIcon()
        icon2.addFile(u"icons/noun-rocket-7158872.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolBox.addItem(self.train_tab, icon2, u"Train model")
        self.predict_tab = QWidget()
        self.predict_tab.setObjectName(u"predict_tab")
        self.predict_tab.setGeometry(QRect(0, 0, 410, 387))
        sizePolicy1.setHeightForWidth(self.predict_tab.sizePolicy().hasHeightForWidth())
        self.predict_tab.setSizePolicy(sizePolicy1)
        icon3 = QIcon()
        icon3.addFile(u"icons/noun-conversion-7158876.svg", QSize(), QIcon.Normal, QIcon.Off)
        self.toolBox.addItem(self.predict_tab, icon3, u"Analyze (new) videos")

        self.mainLayout.addWidget(self.toolBox)

        self.toolBox.raise_()
        self.octron_logo.raise_()

        self.retranslateUi(octron_widgetui)

        self.toolBox.setCurrentIndex(1)
        self.toolBox.layout().setSpacing(10)


        QMetaObject.connectSlotsByName(octron_widgetui)
    # setupUi

    def retranslateUi(self, octron_widgetui):
        octron_widgetui.setWindowTitle(QCoreApplication.translate("octron_widgetui", u"octron_gui", None))
        self.octron_logo.setText("")
        self.toolBox.setItemText(self.toolBox.indexOf(self.project_tab), QCoreApplication.translate("octron_widgetui", u"Project", None))
#if QT_CONFIG(tooltip)
        self.toolBox.setItemToolTip(self.toolBox.indexOf(self.project_tab), QCoreApplication.translate("octron_widgetui", u"Create new octron projects or load existing ones", None))
#endif // QT_CONFIG(tooltip)
        self.horizontalGroupBox.setTitle(QCoreApplication.translate("octron_widgetui", u"Model selection", None))
        self.sam2model_list.setItemText(0, QCoreApplication.translate("octron_widgetui", u"Choose model ...", None))

        self.load_model_btn.setText(QCoreApplication.translate("octron_widgetui", u"Load model", None))
        self.annotate_layer_create_groupbox.setTitle(QCoreApplication.translate("octron_widgetui", u"Layer controls", None))
        self.label_list_combobox.setItemText(0, QCoreApplication.translate("octron_widgetui", u"Label ... ", None))
        self.label_list_combobox.setItemText(1, QCoreApplication.translate("octron_widgetui", u"\u2295 Create", None))
        self.label_list_combobox.setItemText(2, QCoreApplication.translate("octron_widgetui", u"\u2296 Remove", None))

#if QT_CONFIG(tooltip)
        self.label_list_combobox.setToolTip(QCoreApplication.translate("octron_widgetui", u"Select, add or remove labels", None))
#endif // QT_CONFIG(tooltip)
        self.label_list_combobox.setCurrentText(QCoreApplication.translate("octron_widgetui", u"Label ... ", None))
        self.layer_type_combobox.setItemText(0, QCoreApplication.translate("octron_widgetui", u"Type ... ", None))
        self.layer_type_combobox.setItemText(1, QCoreApplication.translate("octron_widgetui", u"Shapes", None))
        self.layer_type_combobox.setItemText(2, QCoreApplication.translate("octron_widgetui", u"Points", None))
        self.layer_type_combobox.setItemText(3, QCoreApplication.translate("octron_widgetui", u"Anchors", None))

        self.layer_type_combobox.setCurrentText(QCoreApplication.translate("octron_widgetui", u"Type ... ", None))
        self.create_annotation_layer_btn.setText(QCoreApplication.translate("octron_widgetui", u"\u2295 Create", None))
#if QT_CONFIG(tooltip)
        self.label_suffix_lineedit.setToolTip(QCoreApplication.translate("octron_widgetui", u"The suffix disambiguates label layers from each other\n"
"that have the same label name.\n"
"For example:\n"
"The label could be octo and suffix 1 for the first octopus,\n"
"and octo and suffix 2 for the second octo ", None))
#endif // QT_CONFIG(tooltip)
        self.label_suffix_lineedit.setPlaceholderText(QCoreApplication.translate("octron_widgetui", u"Suffix", None))
#if QT_CONFIG(tooltip)
        self.hard_reset_layer_btn.setToolTip(QCoreApplication.translate("octron_widgetui", u"Hard reset of the SAM2 predictor. Use this if prediction really did not go well for your data.", None))
#endif // QT_CONFIG(tooltip)
        self.hard_reset_layer_btn.setText(QCoreApplication.translate("octron_widgetui", u"\u3004 Reset", None))
#if QT_CONFIG(tooltip)
        self.create_projection_layer_btn.setToolTip(QCoreApplication.translate("octron_widgetui", u"Create an average projection out of all segmented images for the current label", None))
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(statustip)
        self.create_projection_layer_btn.setStatusTip("")
#endif // QT_CONFIG(statustip)
        self.create_projection_layer_btn.setText(QCoreApplication.translate("octron_widgetui", u"Visualize all", None))
        self.annotate_param_groupbox.setTitle(QCoreApplication.translate("octron_widgetui", u"Parameters", None))
        self.kernel_label.setText(QCoreApplication.translate("octron_widgetui", u"Opening kernel radius", None))
        self.annotate_layer_predict_groupbox.setTitle(QCoreApplication.translate("octron_widgetui", u"Batch prediction", None))
#if QT_CONFIG(tooltip)
        self.batch_predict_progressbar.setToolTip(QCoreApplication.translate("octron_widgetui", u"<html><head/><body><p>Batch predict progress bar</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.batch_predict_progressbar.setFormat(QCoreApplication.translate("octron_widgetui", u"%p%", None))
        self.predict_next_batch_btn.setText("")
        self.annotate_layer_save_groupbox.setTitle(QCoreApplication.translate("octron_widgetui", u"Export training data", None))
#if QT_CONFIG(tooltip)
        self.batch_save_progressbar.setToolTip(QCoreApplication.translate("octron_widgetui", u"<html><head/><body><p>Batch predict progress bar</p></body></html>", None))
#endif // QT_CONFIG(tooltip)
        self.batch_save_progressbar.setFormat(QCoreApplication.translate("octron_widgetui", u"%p%", None))
        self.export_annotations_label.setText(QCoreApplication.translate("octron_widgetui", u"label name", None))
        self.export_annotations_btn.setText(QCoreApplication.translate("octron_widgetui", u"Export\n"
"", None))
        self.toolBox.setItemText(self.toolBox.indexOf(self.annotate_tab), QCoreApplication.translate("octron_widgetui", u"Generate training data (annotate)", None))
#if QT_CONFIG(tooltip)
        self.toolBox.setItemToolTip(self.toolBox.indexOf(self.annotate_tab), QCoreApplication.translate("octron_widgetui", u"Create annotation data for training, i.e. add segmentation or keypoint data on videos.", None))
#endif // QT_CONFIG(tooltip)
        self.toolBox.setItemText(self.toolBox.indexOf(self.train_tab), QCoreApplication.translate("octron_widgetui", u"Train model", None))
#if QT_CONFIG(tooltip)
        self.toolBox.setItemToolTip(self.toolBox.indexOf(self.train_tab), QCoreApplication.translate("octron_widgetui", u"Train a new or existing model with generated training data", None))
#endif // QT_CONFIG(tooltip)
        self.toolBox.setItemText(self.toolBox.indexOf(self.predict_tab), QCoreApplication.translate("octron_widgetui", u"Analyze (new) videos", None))
#if QT_CONFIG(tooltip)
        self.toolBox.setItemToolTip(self.toolBox.indexOf(self.predict_tab), QCoreApplication.translate("octron_widgetui", u"Use trained models to run predictions on new videos", None))
#endif // QT_CONFIG(tooltip)
    # retranslateUi

