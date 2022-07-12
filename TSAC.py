import sys
import json
import threading

from colorama import init, Fore
from datetime import datetime
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import *

from DbWorker import DbWorker

from VIEWS.TSAC.MainWindow import Ui_MainWindow
from VIEWS.TSAC.AdministratorWindow import Ui_AdministratorWindow

init(autoreset=True)

#########################################################################################################
import tkinter
from tkinter import messagebox as mb

import pandastable as pt
import pandas as pd

import MODELS.DBSCAN.Compression as Compression
import MODELS.TSA.TSAModule as TSAModule

from MODELS.DBSCAN.Clustering import DataPreparation, Plot

import numpy as np
tsa = TSAModule.TSA()

SelectedParametersNamesTSA = []
SelectedParametersIndexesTSA = []

plot_window = []
#########################################################################################################

app = QtWidgets.QApplication(sys.argv)

mainUI          = Ui_MainWindow()
administratorUI = Ui_AdministratorWindow()

AdministratorWindow = QtWidgets.QDialog()
MainWindow          = QtWidgets.QMainWindow()

mainUI.setupUi(MainWindow)
administratorUI.setupUi(AdministratorWindow)

def thread(my_func):
    def wrapper(*args):
        my_thread = threading.Thread(target=my_func, args=args)
        my_thread.start()
    return wrapper

dbw = DbWorker()

def openMainWindow():
    initializeActions(mainUI)
    initializeLists(mainUI)
    initializeDates(mainUI)
    MainWindow.show()
def openAdministratorWindow():
    initializeActions(administratorUI)
    initializeLists(administratorUI)
    AdministratorWindow.show()

def initializeDates(ui):
    if type(ui) == Ui_MainWindow:
        ##TSA
        mainUI.FromDateTimeTSA.setDisplayFormat('dd.MM.yyyy hh:mm:ss')
        mainUI.ToDateTimeTSA.setDisplayFormat('dd.MM.yyyy hh:mm:ss')
        mainUI.FromDateTimeTSA.setMinimumDateTime(datetime.strptime(dbw.minDate, '%Y-%m-%d %H:%M:%S'))
        mainUI.ToDateTimeTSA.setMaximumDateTime(datetime.strptime(dbw.maxDate, '%Y-%m-%d %H:%M:%S'))
        mainUI.FromDateTimeTSA.setDateTime(datetime.strptime(dbw.minDate, '%Y-%m-%d %H:%M:%S'))
        mainUI.ToDateTimeTSA.setDateTime(datetime.strptime(dbw.maxDate, '%Y-%m-%d %H:%M:%S'))
def initializeLists(ui):
    if type(ui) == Ui_AdministratorWindow:
        ##TSA
        administratorUI.TimeshiftSpinboxTSA.setValue(tsa.timeshift)
        administratorUI.FeatureExtractionSettingComboboxTSA.addItems(["Извлечение всех характеристик",
                                                                      "Извлечение минимального набора характеристик",
                                                                      "Извлечение предполагаемых эффективных характеристик"])
        administratorUI.FeatureExtractionSettingComboboxTSA.setCurrentIndex(tsa.settingsIndex)
        ##DBSCAN
        administratorUI.nneighboursUMAP.setValue(tsa.nneighboursUMAP)
        administratorUI.minimaldistanseUMAP.setValue(tsa.minimaldistanseUMAP)
        administratorUI.nneighboursDBSCAN.setValue(tsa.nneighboursDBSCAN)
        administratorUI.minimaldistanseDBSCAN.setValue(tsa.minimaldistanseDBSCAN)
    if type(ui) == Ui_MainWindow:
        ##TSA
        items = dbw.getNames(dbw.ruNames, dbw.x)
        outputItems = dbw.getNames(dbw.ruNames, dbw.y)
        outputItems = [x for x in outputItems if str(x) != 'nan']
        for item in items:
            newitem = QListWidgetItem()
            newitem.setText(QApplication.translate("Dialog", item, None))
            newitem.setFlags(newitem.flags() | QtCore.Qt.ItemIsUserCheckable)
            newitem.setCheckState(QtCore.Qt.Unchecked)
            mainUI.ParametersTSA.addItem(newitem)
        for item in outputItems:
            newitem = QListWidgetItem()
            newitem.setText(QApplication.translate("Dialog", item, None))
            mainUI.OutputParametersTSA.addItem(newitem)
        mainUI.ParametersTSA.itemChanged.connect(ParametersSelectionTSA)

def initializeActions(ui):
    if type(ui) == Ui_AdministratorWindow:
        ##TSA
        administratorUI.TimeshiftSpinboxTSA.valueChanged.connect(TimeshiftValueTSA)
        administratorUI.FeatureExtractionSettingComboboxTSA.currentIndexChanged.connect(SettingsValueTSA)
        ##DBSCAN
        administratorUI.nneighboursUMAP.valueChanged.connect(SavePropDBSCAN)
        administratorUI.nneighboursDBSCAN.valueChanged.connect(SavePropDBSCAN)
        administratorUI.minimaldistanseUMAP.valueChanged.connect(SavePropDBSCAN)
        administratorUI.minimaldistanseDBSCAN.valueChanged.connect(SavePropDBSCAN)
    if type(ui) == Ui_MainWindow:
        mainUI.administrator_button.clicked.connect(openAdministratorWindow)
        ##TSA
        mainUI.ClusterDataButtonRAW.clicked.connect(ViewCompresClustersOfBase)
        mainUI.StartButtonTSA.clicked.connect(PrepareDataTSA)
        mainUI.ClusterDataButtonTSA.clicked.connect(ViewCompresClustersOfTSA)
        mainUI.RawDataButtonTSA.clicked.connect(ShowRawDataTSA)
        mainUI.FeaturesDataButtonTSA.clicked.connect(ShowFeaturesTSA)

#########################################################################################################
def SavePropDBSCAN():
    tsa.nneighboursUMAP = administratorUI.nneighboursUMAP.value()
    tsa.minimaldistanseUMAP = administratorUI.minimaldistanseUMAP.value()
    tsa.nneighboursDBSCAN = administratorUI.nneighboursDBSCAN.value()
    tsa.minimaldistanseDBSCAN = administratorUI.minimaldistanseDBSCAN.value()

def ParametersSelectionTSA():
    SelectedParametersNamesTSA.clear()
    SelectedParametersIndexesTSA.clear()
    for i in range(mainUI.ParametersTSA.count() - 1):
        if (mainUI.ParametersTSA.item(i).checkState() == QtCore.Qt.Checked):
            SelectedParametersNamesTSA.append(mainUI.ParametersTSA.item(i).text())
            SelectedParametersIndexesTSA.append(
                list(dbw.ruNames.keys())[list(dbw.ruNames.values()).index(mainUI.ParametersTSA.item(i).text())])\

def PrepareDataTSA():
    try:
        root = tkinter.Tk()
        root.withdraw()
        SelectedOutputParameterIndexTSA = list(dbw.ruNames.keys())[
            list(dbw.ruNames.values()).index(mainUI.OutputParametersTSA.currentItem().text())]
        SelectedOutputParameterNameTSA = mainUI.OutputParametersTSA.currentItem().text()
        defects = pd.DataFrame({str(SelectedOutputParameterNameTSA): pd.Series(dbw.y[SelectedOutputParameterIndexTSA])})
        defects["time"] = pd.Series(dbw.dates)
        timeseries = pd.DataFrame({'time': pd.Series(dbw.dates)})
        indexes = []
        for i in range(timeseries.count()[0]):
            indexes.append("1")
        timeseries["id"] = indexes
        defects["id"] = indexes
        for i in range(len(SelectedParametersIndexesTSA)):
            newparamlist = dbw.x[SelectedParametersIndexesTSA[i]]
            timeseries[SelectedParametersNamesTSA[i]] = newparamlist
        timeseries = timeseries[timeseries['time'].between(str(mainUI.FromDateTimeTSA.dateTime().toPyDateTime()),
                                                           str(mainUI.ToDateTimeTSA.dateTime().toPyDateTime()))]
        defects = defects[defects['time'].between(str(mainUI.FromDateTimeTSA.dateTime().toPyDateTime()),
                                                  str(mainUI.ToDateTimeTSA.dateTime().toPyDateTime()))]
        view_enable = tsa.TimeSeriesAnalyser(timeseries, defects, dbw.limits[SelectedOutputParameterIndexTSA])
        mainUI.ControlPanelTSA.setEnabled(view_enable)
        mainUI.RawDataButtonTSA.setEnabled(view_enable)
        mainUI.RawDataLabelTSA.setEnabled(view_enable)
    except AttributeError:
        mb.showerror("Ошибка", "Вы не выбрали технологический параметр/параметры")
        mainUI.ControlPanelTSA.setEnabled(False)

def TimeshiftValueTSA():
    tsa.timeshift = administratorUI.TimeshiftSpinboxTSA.value()

def SettingsValueTSA():
    tsa.SetSettings(administratorUI.FeatureExtractionSettingComboboxTSA.currentIndex())

def FilterTSA():
    tsa.usefilter = administratorUI.filterTSACheckbox.isChecked()

def ShowRawDataTSA():
    root = tkinter.Tk()
    root.withdraw()
    frame = tkinter.Frame(root)
    frame.pack()
    dTDa1 = tkinter.Toplevel()
    dTDa1.title('Сырые данные')
    ptable = pt.Table(dTDa1, dataframe=tsa.timeseries, showtoolbar=True, showstatusbar=True)
    ptable.show()
    root.mainloop()

def ShowData(_dataframe, name):
    root = tkinter.Tk()
    root.withdraw()
    frame = tkinter.Frame(root)
    frame.pack()
    dTDa1 = tkinter.Toplevel()
    dTDa1.title(name)
    ptable = pt.Table(dTDa1, dataframe=_dataframe, showtoolbar=True, showstatusbar=True)
    ptable.show()
    root.mainloop()

def ShowFeaturesTSA():
    root = tkinter.Tk()
    root.withdraw()
    frame = tkinter.Frame(root)
    frame.pack()
    dTDa1 = tkinter.Toplevel()
    dTDa1.title('Статистические характеристики')
    ptable = pt.Table(dTDa1, dataframe=tsa.filteredfeatures, showtoolbar=True, showstatusbar=True)
    ptable.show()
    root.mainloop()

def ViewCompresClustersOfBase():
    try:
        root = tkinter.Tk()
        root.withdraw()
        SelectedOutputParameterIndexTSA = list(dbw.ruNames.keys())[
            list(dbw.ruNames.values()).index(mainUI.OutputParametersTSA.currentItem().text())]
        SelectedOutputParameterNameTSA = mainUI.OutputParametersTSA.currentItem().text()

        timeseries = pd.DataFrame({'time': pd.Series(dbw.dates)})
        for i in range(len(SelectedParametersIndexesTSA)):
            newparamlist = dbw.x[SelectedParametersIndexesTSA[i]]
            timeseries[SelectedParametersNamesTSA[i]] = newparamlist
        timeseries = timeseries[timeseries['time'].between(str(mainUI.FromDateTimeTSA.dateTime().toPyDateTime()),
                                                           str(mainUI.ToDateTimeTSA.dateTime().toPyDateTime()))]
        defects = [defect[0] for defect in pd.DataFrame({str(SelectedOutputParameterNameTSA): pd.Series(dbw.y[SelectedOutputParameterIndexTSA])}).to_numpy(np.float32)]
        points = np.array(Compression.CompressingData(timeseries.drop(columns=['time']),
                                                      n_neighbors=tsa.nneighboursUMAP,
                                                      min_dist=tsa.minimaldistanseUMAP))
        labels = DataPreparation.GetLabels(points, eps=tsa.minimaldistanseDBSCAN,
                                           min_samples=tsa.nneighboursDBSCAN)
        info = timeseries

        pd.DataFrame(defects, columns=['defects']).to_csv('2.csv', index_label='index')
        timeseries.join(pd.DataFrame(labels, columns=["Кластер"])).to_csv('3.csv', index_label='index')

        Plot.create(points, defects, labels, info, dbw.limits[SelectedOutputParameterIndexTSA])
        plot_window.append(Plot.show())
    except AttributeError:
        mb.showerror("Ошибка", "Вы не выбрали технологический параметр/параметры")

def ViewCompresClustersOfTSA():
    SelectedOutputParameterIndexTSA = list(dbw.ruNames.keys())[
        list(dbw.ruNames.values()).index(mainUI.OutputParametersTSA.currentItem().text())]
    points = np.array(Compression.CompressingData(tsa.filteredfeatures,
                                                  n_neighbors=tsa.nneighboursUMAP,
                                                  min_dist=tsa.minimaldistanseUMAP))
    defects = np.array(np.array(tsa.defects)[len(tsa.defects) - len(points):, 0], dtype=np.float32)

    labels = DataPreparation.GetLabels(points, eps=tsa.minimaldistanseDBSCAN,
                                       min_samples=tsa.nneighboursDBSCAN)
    info = tsa.timeseries.drop(columns=['id'])[len(tsa.defects) - len(points):].reset_index(drop=True)

    pd.DataFrame(defects, columns=['defects']).to_csv('2.csv', index_label='index')
    tsa.timeseries.drop(columns=['id'])[len(tsa.defects) - len(points):].reset_index(drop=True).join(
        tsa.filteredfeatures.reset_index(drop=True)).join(
        pd.DataFrame(labels, columns=["Кластер"])).to_csv('3.csv', index_label='index')

    Plot.create(points, defects, labels, info, dbw.limits[SelectedOutputParameterIndexTSA])
    plot_window.append(Plot.show())
#########################################################################################################

def loadData():
    file = open('settings.json')
    dates = json.load(file)
    print("Начало загрузки данных...")
    dbw.loadData(str(dates['FromDateTime']), str(dates['ToDateTime']))
    print(Fore.GREEN + "Данные успешно загружены")

def addCheckableItems(ui, items):
    for item in items:
        newItem = QListWidgetItem()
        newItem.setText(item)
        newItem.setFlags(newItem.flags() | QtCore.Qt.ItemIsUserCheckable)
        newItem.setCheckState(QtCore.Qt.Unchecked)
        ui.addItem(newItem)
def getCheckedParameters(ui):
    result = list()
    for i in range(ui.count() - 1):
        if (ui.item(i).checkState() == QtCore.Qt.Checked):
            result.append(ui.item(i).text())
    return result

if __name__ == "__main__":
    loadData()
    if dbw.isDataLoaded:
        openMainWindow()
        sys.exit(app.exec_())
    else:
        sys.exit()