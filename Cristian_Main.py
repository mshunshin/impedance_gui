import os
import sys

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

from pathlib import Path

from scipy import stats

from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSplitter, QLabel

import imp
from imp.reader import Sciospec
from imp.bpecg import Nova
#import sciopy as Sciospec
#from nova_client import NOVAClient as Nova

import pyqtgraph as pg

#from cyclopts import App

#cl_app = App()


class Startup(QtWidgets.QMainWindow):
    def __init__(self, data_dir: Path = None):
        super().__init__()
        self.region_item = pg.LinearRegionItem()

        # Create a QPushButton object and set its properties
        self.setWindowTitle("Welcome to use Impedance Analysis GUI")
        self.data_dir = Path(data_dir)
        self.detect_path()
        button1 = QtWidgets.QPushButton("Select Patient Data Folder for Impedance Analysis")
        button1.setToolTip("Good Luck with your data analysis")
        self.selected_directory = button1.clicked.connect(self.select_folder)
        button2 = QtWidgets.QPushButton("Exit")
        button2.clicked.connect(self.exitbutton)
        button3 = QtWidgets.QPushButton("See all patients' tilt")
        button3.clicked.connect(self.tilt_baseline)

        # Add the button to the main window
        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(button1)
        layout.addWidget(button3)
        layout.addWidget(button2)

        # Create a QWidget and set its layout to the QHBoxLayout
        widget = QtWidgets.QWidget()
        widget.setLayout(layout)

        # Set the widget as the central widget of the main window
        self.setCentralWidget(widget)
        self.new_windows = []

    def detect_path(self):
        if self.data_dir.exists():
            os.chdir(self.data_dir)
        else:
            path = os.getcwd()
            parent = os.path.dirname(path)
            os.chdir(str(parent) + "/Data")

    def select_folder(self):
        self.selected_directory = QtWidgets.QFileDialog.getExistingDirectory()
        print('selected_directory:', self.selected_directory)
        if self.selected_directory == "":
            QtCore.QCoreApplication.quit()
        window = Analysis(self.selected_directory)
        window.showMaximized()
        self.new_windows.append(window)

    def tilt_baseline(self):
        self.selected_directory = QtWidgets.QFileDialog.getExistingDirectory()
        print('selected_directory:', self.selected_directory)
        for i in range(2):
            # i=1
            if i == 0:
                contains_string = "+"
            else:
                contains_string = "-"
            folders = [folder for folder in os.listdir(self.selected_directory) if
                       contains_string in folder and os.path.isdir(os.path.join(self.selected_directory, folder))]
            fig, axs = plt.subplots(nrows=1, ncols=3)
            c = 0
            patient_num = []
            rel_imp1 = []
            rel_imp2 = []
            rel_imp3 = []
            rel_hrv = []
            rel_hr = []
            rel_map = []
            rel_pp = []
            for folder_name in folders:
                folder = os.path.join(self.selected_directory, folder_name)
                print(f"Processing folder: {folder}")
                print(f"The last letter of foler is {folder[-1]}")
                self.bpecg = Nova(folder)
                if folder[-1] != "T":
                    self.three_channel = False
                    GROUP_1 = 'EXT2 1 2 5 6'
                    GROUP_2 = 'EXT2 9 10 13 14'
                    data_folder_1 = Path(folder) / 'setup_00001' / GROUP_1
                    data_folder_2 = Path(folder) / 'setup_00001' / GROUP_2

                    self.imp1 = Sciospec(data_folder_1, 1)
                    self.imp2 = Sciospec(data_folder_2, 2)
                    if self.imp1.freq.all() != 0 and self.imp2.freq.all() != 0:
                        print("import 2 channels of imp successfully")
                if folder[-1] == "T":
                    self.three_channel = True
                    GROUP_1 = 'EXT2 1 2 5 6'
                    GROUP_2 = 'EXT2 9 10 11 12'
                    GROUP_3 = 'EXT2 13 14 15 16'
                    data_folder_1 = Path(folder) / 'setup_00001' / GROUP_1
                    data_folder_2 = Path(folder) / 'setup_00001' / GROUP_2
                    data_folder_3 = Path(folder) / 'setup_00001' / GROUP_3
                    self.imp1 = Sciospec(data_folder_1, 1)
                    self.imp2 = Sciospec(data_folder_2, 2)
                    self.imp3 = Sciospec(data_folder_3, 3)
                    if self.imp1.freq.all() != 0 and self.imp2.freq.all() != 0:
                        print("import 3 channels of imp successfully")

                self.imp_analysis()
                self.bpecg.maptime = np.array(self.bpecg.maptime)
                self.bpecg.hrtime = np.array(self.bpecg.hrtime)
                self.bpecg.aptime = np.array(self.bpecg.aptime)
                self.bpecg.systime = np.array(self.bpecg.systime)
                self.bpecg.diatime = np.array(self.bpecg.diatime)
                ref_min = np.argmin(np.abs(self.imp1.timestamps - (self.imp1.t_tilted + 30)))
                ref_max = np.argmin(np.abs(self.imp1.timestamps - (self.imp1.t_tilted + 90)))
                ref_hr_min = np.argmin(np.abs(self.bpecg.hrtime - (self.imp1.t_tilted + 30)))
                ref_hr_max = np.argmin(np.abs(self.bpecg.hrtime - (self.imp1.t_tilted + 90)))
                ref_map_min = np.argmin(np.abs(self.bpecg.maptime - (self.imp1.t_tilted + 30)))
                ref_map_max = np.argmin(np.abs(self.bpecg.maptime - (self.imp1.t_tilted + 90)))
                ref_sys_min = np.argmin(np.abs(self.bpecg.systime - (self.imp1.t_tilted + 30)))
                ref_sys_max = np.argmin(np.abs(self.bpecg.systime - (self.imp1.t_tilted + 90)))
                ref_dia_min = np.argmin(np.abs(self.bpecg.diatime - (self.imp1.t_tilted + 30)))
                ref_dia_max = np.argmin(np.abs(self.bpecg.diatime - (self.imp1.t_tilted + 90)))
                # print(f't_tilt is {self.imp1.t_tilted}\nref_min is {ref_min}\nref_max is {ref_max} min '
                #       f'is {self.imp1.timestamps[ref_min]}\nThe other is {self.imp1.timestamps[ref_max]}')
                baseline1 = np.mean(self.imp1_m[ref_min:ref_max])
                # print(baseline1)
                baseline2 = np.mean(self.imp2_m[ref_min:ref_max])
                baseline_hrv = np.mean(self.bpecg.hrv[ref_hr_min:ref_hr_max])
                baseline_hr = np.mean(self.bpecg.hr[ref_hr_min:ref_hr_max])
                baseline_map = np.mean(self.bpecg.mapfi[ref_map_min:ref_map_max])
                baseline_sys = np.mean(self.bpecg.sysfi[ref_sys_min:ref_sys_max])
                baseline_dia = np.mean(self.bpecg.diafi[ref_dia_min:ref_dia_max])
                # after5 = np.argmin(np.abs(self.imp1.timestamps - (self.imp1.t_tilted + 300)))
                # x = self.imp1.timestamps[ref_max:after5] - self.imp1.timestamps[ref_max]
                before_faint_10s_ind = np.argmin(np.abs(self.imp1.timestamps - (self.imp1.t_end - 10)))
                before_faint_10s_ind_hrv = np.argmin(np.abs(self.bpecg.hrtime - (self.imp1.t_end - 10)))
                before_faint_10s_ind_map = np.argmin(np.abs(self.bpecg.maptime - (self.imp1.t_end - 10)))
                before_faint_10s_ind_sys = np.argmin(np.abs(self.bpecg.systime - (self.imp1.t_end - 10)))
                before_faint_10s_ind_dia = np.argmin(np.abs(self.bpecg.diatime - (self.imp1.t_end - 10)))
                faint_ind = np.argmin(np.abs(self.imp1.timestamps - self.imp1.t_end + 5))
                faint_ind_hrv = np.argmin(np.abs(self.bpecg.hrtime - self.imp1.t_end + 5))
                faint_ind_map = np.argmin(np.abs(self.bpecg.maptime - self.imp1.t_end + 5))
                faint_ind_sys = np.argmin(np.abs(self.bpecg.systime - self.imp1.t_end + 5))
                faint_ind_dia = np.argmin(np.abs(self.bpecg.diatime - self.imp1.t_end + 5))
                comparing_method = '10s_mean'
                if comparing_method == '10s_mean':
                    rel_before_faint_imp1 = (np.mean(self.imp1_m[before_faint_10s_ind:faint_ind])/baseline1)*100-100
                    rel_before_faint_imp2 = (np.mean(self.imp2_m[before_faint_10s_ind:faint_ind])/baseline2)*100-100
                    rel_before_faint_hrv = (np.mean(
                        self.bpecg.hrv[before_faint_10s_ind_hrv:faint_ind_hrv]) / baseline_hrv) * 100 - 100
                    rel_before_faint_hr = (np.mean(
                        self.bpecg.hr[before_faint_10s_ind_hrv:faint_ind_hrv]) / baseline_hr) * 100 - 100
                    rel_before_faint_map = (np.mean(
                        self.bpecg.mapfi[before_faint_10s_ind_map:faint_ind_map]) / baseline_map) * 100 - 100
                    rel_before_faint_sys = (np.mean(
                        self.bpecg.sysfi[before_faint_10s_ind_sys:faint_ind_sys]) / baseline_sys) * 100 - 100
                    rel_before_faint_dia = (np.mean(
                        self.bpecg.diafi[before_faint_10s_ind_dia:faint_ind_dia]) / baseline_dia) * 100 - 100
                    try:
                        baseline3 = np.mean(self.imp3_m[ref_min:ref_max])
                        rel_before_faint_imp3 = (np.mean(
                            self.imp3_m[before_faint_10s_ind:faint_ind]) / baseline3) * 100 - 100
                        rel_imp3.append(rel_before_faint_imp3)
                    except:
                        rel_imp3.append(np.nan)
                if comparing_method == 'max':
                    imp1_for_max = self.imp1_m[ref_max:faint_ind]
                    imp2_for_max = self.imp2_m[ref_max:faint_ind]
                    hrv_for_max = self.bpecg.hrv[ref_hr_max:faint_ind_hrv]
                    hr_for_max = self.bpecg.hr[ref_hr_max:faint_ind_hrv]
                    map_for_max = self.bpecg.mapfi[ref_map_max:faint_ind_map]
                    sys_for_max = self.bpecg.sysfi[ref_sys_max:faint_ind_sys]
                    dia_for_max = self.bpecg.diafi[ref_dia_max:faint_ind_dia]
                    rel_before_faint_imp1 = imp1_for_max[np.argmax(np.abs(
                        imp1_for_max - baseline1))]/baseline1 * 100 - 100
                    rel_before_faint_imp2 = imp2_for_max[np.argmax(np.abs(
                        imp2_for_max - baseline2))] / baseline2 * 100 - 100
                    rel_before_faint_hrv = hrv_for_max[np.argmax(np.abs(
                        hrv_for_max - baseline_hrv))] / baseline_hrv * 100 - 100
                    rel_before_faint_hr = hr_for_max[np.argmax(np.abs(
                        hr_for_max - baseline_hr))] / baseline_hr * 100 - 100
                    rel_before_faint_map = map_for_max[np.argmax(np.abs(
                        map_for_max - baseline_map))] / baseline_map * 100 - 100
                    rel_before_faint_sys = sys_for_max[np.argmax(np.abs(
                        sys_for_max - baseline_sys))] / baseline_sys * 100 - 100
                    rel_before_faint_dia = dia_for_max[np.argmax(np.abs(
                        dia_for_max - baseline_dia))] / baseline_dia * 100 - 100
                    try:
                        imp3_for_max = self.imp3_m[ref_max:faint_ind]
                        baseline3 = np.mean(self.imp3_m[ref_min:ref_max])
                        rel_before_faint_imp3 = imp3_for_max[np.argmax(np.abs(
                        imp3_for_max - baseline3))] / baseline3 * 100 - 100
                        rel_imp3.append(rel_before_faint_imp3)
                    except:
                        rel_imp3.append(np.nan)
                # print(f'rel imp 1: {rel_before_faint_imp1} %\n'
                #       f'rel imp 2: {rel_before_faint_imp2} %')
                patient_num.append(folder_name)
                rel_imp1.append(rel_before_faint_imp1)
                rel_imp2.append(rel_before_faint_imp2)
                rel_hrv.append(rel_before_faint_hrv)
                rel_hr.append(rel_before_faint_hr)
                rel_map.append(rel_before_faint_map)
                rel_pp.append(rel_before_faint_sys-rel_before_faint_dia)

                # axs[0].plot(x, (self.imp1_m[ref_max:after5]/baseline1-1)*100)
                # axs[0].set_title(f'Overlapping thoracic impedance % change after tilt')
                # axs[1].plot(x, (self.imp2_m[ref_max:after5]/baseline2-1)*100)
                # axs[1].set_title(f'Overlapping splanchnic impedance % change after tilt')
                # axs[0].set_ylabel('Percentage %')
                # axs[1].set_ylabel('Percentage %')
                c = c+1

            if i == 0:
                self.rel_imp_df_pos = pd.DataFrame(
                    {'Patient info': patient_num, 'relative thoracic impedance change %': rel_imp1,
                     'relative splanchnic impedance change %': rel_imp2,
                     'relative thigh impedance change %': rel_imp3,
                     'relative hr change %': rel_hr, 'relative map change %': rel_map,
                     'relative pulse pressure change %': rel_pp})
                rel_imp_df = self.rel_imp_df_pos
                self.rel_imp_df_pos.to_excel(excel_writer = "D:\Impedance_Measurements\Data/relative impedance 5-10 change pos.xlsx")
            if i == 1:
                self.rel_imp_df_neg = pd.DataFrame(
                    {'Patient info': patient_num, 'relative thoracic impedance change %': rel_imp1,
                     'relative splanchnic impedance change %': rel_imp2,
                     'relative thigh impedance change %': rel_imp3,
                     'relative hr change %': rel_hr, 'relative map change %': rel_map,
                     'relative pulse pressure change %': rel_pp})
                rel_imp_df = self.rel_imp_df_neg
                self.rel_imp_df_neg.to_excel(excel_writer="D:\Impedance_Measurements\Data/relative impedance 5-10 change neg.xlsx")

            # os.chdir(self.selected_directory)
            # fig.set_size_inches(w=25, h=15)
            # fig.savefig(f'figure.png', format='png', dpi=1200)
            sns.boxplot(data=rel_imp_df,y='relative thoracic impedance change %',color='lightblue',ax=axs[0],showfliers=False)
            sns.stripplot(data=rel_imp_df,y='relative thoracic impedance change %',color='red',jitter=True,size=4,ax=axs[0])
            sns.boxplot(data=rel_imp_df, y='relative splanchnic impedance change %', color='lightblue',ax=axs[1],showfliers=False)
            sns.stripplot(data=rel_imp_df, y='relative splanchnic impedance change %', color='red', jitter=True, size=4,ax=axs[1])
            sns.boxplot(data=rel_imp_df, y='relative thigh impedance change %', color='lightblue', ax=axs[2],showfliers=False)
            sns.stripplot(data=rel_imp_df, y='relative thigh impedance change %', color='red', jitter=True, size=4,
                          ax=axs[2])
            fig, axs = plt.subplots(nrows=1, ncols=3)
            sns.boxplot(data=rel_imp_df, y='relative hr change %', color='lightblue', ax=axs[0],
                        showfliers=False)
            sns.stripplot(data=rel_imp_df, y='relative hr change %', color='red', jitter=True, size=4,
                          ax=axs[0])
            sns.boxplot(data=rel_imp_df, y='relative map change %', color='lightblue', ax=axs[1],
                        showfliers=False)
            sns.stripplot(data=rel_imp_df, y='relative map change %', color='red', jitter=True, size=4,
                          ax=axs[1])
            sns.boxplot(data=rel_imp_df, y='relative pulse pressure change %', color='lightblue', ax=axs[2],
                        showfliers=False)
            sns.stripplot(data=rel_imp_df, y='relative pulse pressure change %', color='red', jitter=True, size=4,
                          ax=axs[2])
        # stat, p_thoracic = stats.shapiro(
        #     self.rel_imp_df_neg['relative thoracic impedance change %'] - self.rel_imp_df_pos[
        #         'relative thoracic impedance change %'])
        # stat, p_splanchnic = stats.shapiro(
        #     self.rel_imp_df_neg['relative splanchnic impedance change %'] - self.rel_imp_df_pos[
        #         'relative splanchnic impedance change %'])
        # stat, p_thigh = stats.shapiro(
        #     self.rel_imp_df_neg['relative thigh impedance change %'] - self.rel_imp_df_pos[
        #         'relative thigh impedance change %'])
        # print(f'Thoracic P = {p_thoracic}, Splanchnic P = {p_splanchnic}, Thigh P = {p_thigh}')
        plt.show()

    def imp_analysis(self):
        freqwanted = 50000
        input_freq = float(freqwanted)
        imp1_freq_idx = np.argmin(np.abs(self.imp1.freq - input_freq))
        imp2_freq_idx = np.argmin(np.abs(self.imp2.freq - input_freq))

        AvgAbsImp1 = self.imp1.abs_ohm_np[:, imp1_freq_idx]
        AvgAbsImp2 = self.imp2.abs_ohm_np[:, imp2_freq_idx]

        ZImp1 = stats.zscore(AvgAbsImp1)
        ZImp2 = stats.zscore(AvgAbsImp2)
        threshold = 3
        outlier1 = np.concatenate(np.where(ZImp1 > threshold))
        outlier2 = np.concatenate(np.where(ZImp2 > threshold))
        AvgAbsImp1NoOL = AvgAbsImp1
        AvgAbsImp2NoOL = AvgAbsImp2
        for ind in outlier1:
            if 1 <= ind < len(AvgAbsImp1NoOL) - 1:
                AvgAbsImp1NoOL[ind] = np.mean(np.array(AvgAbsImp1NoOL[ind - 1], AvgAbsImp1NoOL[ind + 1]))
            elif ind == 0:
                AvgAbsImp1NoOL[ind] = AvgAbsImp1NoOL[ind + 1]
            else:
                AvgAbsImp1NoOL[ind] = AvgAbsImp1NoOL[ind - 1]
        for ind in outlier2:
            if 1 <= ind < len(AvgAbsImp2NoOL) - 1:
                AvgAbsImp2NoOL[ind] = np.mean(np.array(AvgAbsImp2NoOL[ind - 1], AvgAbsImp2NoOL[ind + 1]))
            elif ind == 0:
                AvgAbsImp2NoOL[ind] = AvgAbsImp2NoOL[ind + 1]
            else:
                AvgAbsImp2NoOL[ind] = AvgAbsImp2NoOL[ind - 1]

        fs1 = self.imp1.filenum / (self.imp1.timestamps[-1] - self.imp1.timestamps[0])
        fs2 = self.imp2.filenum / (self.imp2.timestamps[-1] - self.imp2.timestamps[0])
        self.imp1_m=AvgAbsImp1NoOL
        self.imp2_m=AvgAbsImp2NoOL
        if self.three_channel == True:
            imp3_freq_idx = np.argmin(np.abs(self.imp3.freq - input_freq))
            AvgAbsImp3 = self.imp3.abs_ohm_np[:, imp3_freq_idx]
            ZImp3 = stats.zscore(AvgAbsImp2)
            outlier3 = np.concatenate(np.where(ZImp3 > threshold))
            AvgAbsImp3NoOL = AvgAbsImp3
            for ind in outlier3:
                if 1 <= ind < len(AvgAbsImp3NoOL) - 1:
                    AvgAbsImp3NoOL[ind] = np.mean(np.array(AvgAbsImp3NoOL[ind - 1], AvgAbsImp3NoOL[ind + 1]))
                elif ind == 0:
                    AvgAbsImp3NoOL[ind] = AvgAbsImp3NoOL[ind + 1]
                else:
                    AvgAbsImp3NoOL[ind] = AvgAbsImp3NoOL[ind - 1]
            fs3 = self.imp3.filenum / (self.imp3.timestamps[-1] - self.imp3.timestamps[0])
            self.imp3_m = AvgAbsImp3NoOL

    def exitbutton(self):
        QtCore.QCoreApplication.quit()


class Analysis(QtWidgets.QMainWindow):
    def __init__(self, folder):
        super().__init__()
        self.setWindowTitle("Impedance Analysis GUI")

        # Create the main widget and set it as the central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create the layout for the main widget
        layout = QVBoxLayout(central_widget)

        # Create the splitter
        splitter = QSplitter()

        # Create the plot widget
        self.bpecg=Nova(folder)
        print(f'SYSfi is {self.bpecg.sysfi[1:10]}')
        print(f'DIAfi is {self.bpecg.diafi[1:10]}')
        print(f'MAPfi is {self.bpecg.mapfi[1:10]}')
        if self.bpecg.diafi!=0:
            print("import bpecg successfully")

        if folder[-1] != "T":
            self.three_channel = False
            GROUP_1 = 'EXT2 1 2 5 6'
            GROUP_2 = 'EXT2 9 10 13 14'
            data_folder_1 = Path(folder) / 'setup_00001' / GROUP_1
            data_folder_2 = Path(folder) / 'setup_00001' / GROUP_2

            self.imp1 = Sciospec(data_folder_1, 1)
            self.imp2 = Sciospec(data_folder_2, 2)
            if self.imp1.freq.all() != 0 and self.imp2.freq.all() != 0:
                print("import 2 channels of imp successfully")
        if folder[-1] == "T":
            self.three_channel = True
            GROUP_1 = 'EXT2 1 2 5 6'
            GROUP_2 = 'EXT2 9 10 11 12'
            GROUP_3 = 'EXT2 13 14 15 16'
            data_folder_1 = Path(folder) / 'setup_00001' / GROUP_1
            data_folder_2 = Path(folder) / 'setup_00001' / GROUP_2
            data_folder_3 = Path(folder) / 'setup_00001' / GROUP_3
            self.imp1 = Sciospec(data_folder_1, 1)
            self.imp2 = Sciospec(data_folder_2, 2)
            self.imp3 = Sciospec(data_folder_3, 3)
            if self.imp1.freq.all() != 0 and self.imp2.freq.all() != 0:
                print("import 3 channels of imp successfully")

        self.imp_analysis()

        if folder[-1] != "T":
            imp_df = pd.DataFrame({
                'timestamp': self.imp1.timestamps,
                'imp1': self.imp1_m,
                'imp2': self.imp2_m
            })
            imp_df.to_excel(excel_writer=folder + '/impfile/imp.xlsx')

        if folder[-1] == "T":
            imp_df = pd.DataFrame({
                'timestamp': self.imp1.timestamps,
                'imp1': self.imp1_m,
                'imp2': self.imp2_m,
                'imp3': self.imp3_m
            })
            imp_df.to_excel(excel_writer=folder + '/impfile/imp.xlsx')

        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)

        self.plot1 = pg.PlotWidget()
        self.plot2 = pg.PlotWidget()
        self.plot3 = pg.PlotWidget()
        self.plot4 = pg.PlotWidget()
        self.plot5 = pg.PlotWidget()
        self.plot6 = pg.PlotWidget()
        plot_list = [self.plot1, self.plot2, self.plot3, self.plot4, self.plot5, self.plot6]

        if self.three_channel:
            self.plot7 = pg.PlotWidget()
            plot_list.append(self.plot7)

        for plot in plot_list:
            if hasattr(self.imp1, 't_tilted'):
                v_tilt = pg.InfiniteLine(pos=self.imp1.t_tilted, angle=90, movable=False)
                plot.addItem(v_tilt)
                label = pg.TextItem(text="Tilt")
                diff = [x - self.imp1.t_tilted for x in self.bpecg.maptime]
                time_index = np.argmin(np.abs(diff))
                label.setPos(self.imp1.t_tilted, self.bpecg.mapfi[time_index])
                plot.addItem(label)

            if hasattr(self.imp1, 't_gtn'):
                v_gtn = pg.InfiniteLine(pos=self.imp1.t_gtn, angle=90, movable=False)
                plot.addItem(v_gtn)
                label = pg.TextItem(text="GTN")
                diff = [x - self.imp1.t_gtn for x in self.bpecg.maptime]
                time_index = np.argmin(np.abs(diff))
                label.setPos(self.imp1.t_gtn, self.bpecg.mapfi[time_index])
                plot.addItem(label)

            if hasattr(self.imp1, 't_end'):
                v_end = pg.InfiniteLine(pos=self.imp1.t_end, angle=90, movable=False)
                plot.addItem(v_end)
                label = pg.TextItem(text="EoT")
                diff = [x - self.imp1.t_end for x in self.bpecg.maptime]
                time_index = np.argmin(np.abs(diff))
                label.setPos(self.imp1.t_end, self.bpecg.mapfi[time_index])
                plot.addItem(label)

        self.plot1.plot(self.bpecg.maptime, self.bpecg.mapfi)
        self.plot1.setFixedHeight(int(self.height() * 0.1))

        self.plot2.setTitle('MAP', bold=1, size="20pt")
        self.plot2.plot(self.bpecg.maptime, self.bpecg.mapfi)

        self.plot3.setTitle('Thoracic Impedance', bold=1, size="20pt")
        self.plot3.plot(self.imp1.timestamps, self.imp1_m)
        self.plot3.setYRange(min(self.imp1_m), max(self.imp1_m))
        self.plot3.setXLink(self.plot2)

        self.plot4.setTitle('Splanchnic Impedance', bold=1, size="20pt")
        self.plot4.plot(self.imp2.timestamps, self.imp2_m)
        self.plot4.setYRange(min(self.imp2_m), max(self.imp2_m))
        self.plot4.setXLink(self.plot2)

        self.plot5.setTitle('Heart Rate', bold=1, size="20pt")
        self.plot5.plot(self.bpecg.hrtime, self.bpecg.hr)
        self.plot5.setXLink(self.plot2)

        self.plot6.setTitle('Beat-Beat Blood Pressure', bold=1, size="20pt")
        self.plot6.plot(self.bpecg.aptime, self.bpecg.ap)

        plot_layout.addWidget(self.plot1)
        plot_layout.addWidget(self.plot3)
        plot_layout.addWidget(self.plot4)

        if self.three_channel:
            self.plot7.plot(self.imp3.timestamps, self.imp3_m)
            self.plot7.setYRange(min(self.imp3_m), max(self.imp3_m))
            self.plot7.setTitle('Thigh Impedance', bold=1, size="20pt")
            plot_layout.addWidget(self.plot7)

        plot_layout.addWidget(self.plot5)
        plot_layout.addWidget(self.plot6)
        plot_layout.addWidget(self.plot2)

        self.bpecg.maptime = np.array(self.bpecg.maptime)
        self.bpecg.hrtime = np.array(self.bpecg.hrtime)
        self.bpecg.aptime = np.array(self.bpecg.aptime)
        self.bpecg.systime = np.array(self.bpecg.systime)
        self.bpecg.diatime = np.array(self.bpecg.diatime)

        # self.proxy = pg.SignalProxy(self.plot3.scene().sigMouseMoved, rateLimit=60, slot=self.mouseMoved)
        #
        # self.label = pg.TextItem(anchor=(0, 1))
        # self.plot3.addItem(self.label)

        # Add the selection region
        self.plot1.setXRange(min(self.bpecg.maptime), max(self.bpecg.maptime))
        self.plot2.setYRange(min(self.bpecg.mapfi), max(self.bpecg.mapfi))
        self.selection_region = pg.LinearRegionItem()
        self.plot1.addItem(self.selection_region)

        # Connect the region changed signal to update the second plot
        self.selection_region.sigRegionChanged.connect(self.update_plot2)

        # Create the left widget (side panel)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        button1 = QtWidgets.QPushButton("6-second window average")
        button1.clicked.connect(self.select6)
        button2 = QtWidgets.QPushButton("See relevant changes--Set baseline")
        button2.clicked.connect(self.selectR)
        button3 = QtWidgets.QPushButton("See relevant changes--Select Datapoint")
        button3.clicked.connect(self.selectI)
        button4 = QtWidgets.QPushButton(f"Plot bar chart between Tilt+90 and EoT")
        button4.clicked.connect(self.barchart)
        left_layout.addWidget(button1)
        left_layout.addWidget(button2)
        left_layout.addWidget(button3)
        left_layout.addWidget(button4)
        self.imp1avg6label = QLabel()
        left_layout.addWidget(self.imp1avg6label)
        self.relative_change_label = QLabel()
        left_layout.addWidget(self.relative_change_label)
        bottom_panel = QLabel("Zhuang Liu\nDepartment of Bioengineering\nImperial College London")
        bottom_panel.setFixedHeight(int(self.height() * 0.1))
        left_layout.addWidget(bottom_panel)

        # Add the left and right widgets to the splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(plot_widget)

        # Set the initial sizes of the widgets
        splitter.setSizes([int(self.width() * 0.1), int(self.width() * 0.9)])

        # Set the splitter as the central widget of the main window
        layout.addWidget(splitter)

        # Relative change calculation and illustration
        # baseline_ind1 = np.argmin(np.abs(self.imp1.t_tilted + 30 - self.imp1.timestamps))
        # baseline_ind2 = np.argmin(np.abs(self.imp1.t_tilted + 90 - self.imp1.timestamps))
        # baseline_ind_sys1 = np.argmin(np.abs(self.imp1.t_tilted - 30 - self.bpecg.systime))
        # baseline_ind_sys2 = np.argmin(np.abs(self.imp1.t_tilted - self.bpecg.systime))
        # baseline_ind_hr1 = np.argmin(np.abs(self.imp1.t_tilted - 30 - self.bpecg.hrtime))
        # baseline_ind_hr2 = np.argmin(np.abs(self.imp1.t_tilted - self.bpecg.hrtime))
        # baseline_ind_pp1 = np.argmin(np.abs(self.imp1.t_tilted - 30 - self.bpecg.systime))
        # baseline_ind_pp2 = np.argmin(np.abs(self.imp1.t_tilted - self.bpecg.systime))
        #
        # baseline1 = np.mean(self.imp1_m[baseline_ind1:baseline_ind2])
        # baseline2 = np.mean(self.imp2_m[baseline_ind1:baseline_ind2])
        # baseline_sys = np.mean(self.bpecg.sysfi[baseline_ind_sys1:baseline_ind_sys2])
        # baseline_hr = np.mean(self.bpecg.hr[baseline_ind_hr1:baseline_ind_hr2])
        # baseline_pp = np.mean(self.bpecg.pp[baseline_ind_pp1:baseline_ind_pp2])
        #
        # data_ind_sys1 = np.argmin(np.abs(self.imp1.t_tilted + 0 - self.bpecg.systime))
        # data_ind_sys2 = np.argmin(np.abs(self.imp1.t_end - self.bpecg.systime))
        # data_ind_hr1 = np.argmin(np.abs(self.imp1.t_tilted + 0 - self.bpecg.hrtime))
        # data_ind_hr2 = np.argmin(np.abs(self.imp1.t_end - self.bpecg.hrtime))
        # data_ind_pp1 = data_ind_sys1
        # data_ind_pp2 = data_ind_sys2
        # data_sys = np.divide(self.bpecg.sysfi[data_ind_sys1:data_ind_sys2], baseline_sys)
        # data_hr = np.divide(self.bpecg.hr[data_ind_hr1:data_ind_hr2], baseline_hr)
        # data_pp = np.divide(self.bpecg.pp[data_ind_pp1:data_ind_pp2], baseline_pp)
        #
        # avg_window = 10
        # y1 = []
        # y2 = []
        # current_ind = baseline_ind2
        # next_ind = []
        # while current_ind <= np.argmin(np.abs(self.imp1.t_end - 0 - avg_window - self.imp1.timestamps)):
        #     next_ind = np.argmin(np.abs(self.imp1.timestamps - (self.imp1.timestamps[current_ind] + avg_window)))
        #     y1.append(np.mean(self.imp1_m[current_ind:next_ind]))
        #     y2.append(np.mean(self.imp2_m[current_ind:next_ind]))
        #     current_ind = next_ind
        # x = np.arange(0, len(y1) * avg_window, avg_window) + 90
        #
        # print(f'The thoracic impedance baseline is {baseline1}\n'
        #       f'The thoracic impedance when faint is {y1[-1]}\n'
        #       f'The thoracic relative change is {(y1[-1]-baseline1)/baseline1}\n'
        #       f'The splanchnic impedance baseline is {baseline2}\n'
        #       f'The splanchnic impedance when faint is {y2[-1]}\n'
        #       f'The splanchnic relative change is {(y2[-1]-baseline2)/baseline2}\n')
        #
        # df = pd.DataFrame(columns=['Thoracic impedance baseline','Thoracic impedance at faint',
        #                            'Thoracic relative imp change','Splanchnic Impedance baseline',
        #                            'splanchnic impedance at faint','splanchnic relative imp change'])

    def barchart(self):

        baseline_ind1 = np.argmin(np.abs(self.imp1.t_tilted + 30 - self.imp1.timestamps))
        baseline_ind2 = np.argmin(np.abs(self.imp1.t_tilted + 90 - self.imp1.timestamps))
        baseline_ind_sys1 = np.argmin(np.abs(self.imp1.t_tilted - 30 - self.bpecg.systime))
        baseline_ind_sys2 = np.argmin(np.abs(self.imp1.t_tilted - self.bpecg.systime))
        baseline_ind_hr1 = np.argmin(np.abs(self.imp1.t_tilted - 30 - self.bpecg.hrtime))
        baseline_ind_hr2 = np.argmin(np.abs(self.imp1.t_tilted - self.bpecg.hrtime))
        baseline_ind_pp1 = np.argmin(np.abs(self.imp1.t_tilted - 30 - self.bpecg.systime))
        baseline_ind_pp2 = np.argmin(np.abs(self.imp1.t_tilted - self.bpecg.systime))


        # print(f'baseline_ind_sys is {baseline_ind_sys}\n'
        #       f't_tilt time is {self.imp1.t_tilted}\n'
        #       f'returned time is {self.bpecg.systime[baseline_ind_sys]}')
        # eot_ind = np.argmin(np.abs(self.imp1.t_end - self.imp1.timestamps))
        baseline1 = np.mean(self.imp1_m[baseline_ind1:baseline_ind2])
        baseline2 = np.mean(self.imp2_m[baseline_ind1:baseline_ind2])
        baseline_sys = np.mean(self.bpecg.sysfi[baseline_ind_sys1:baseline_ind_sys2])
        baseline_hr = np.mean(self.bpecg.hr[baseline_ind_hr1:baseline_ind_hr2])
        baseline_pp = np.mean(self.bpecg.pp[baseline_ind_pp1:baseline_ind_pp2])

        data_ind_sys1 = np.argmin(np.abs(self.imp1.t_tilted + 0 - self.bpecg.systime))
        data_ind_sys2 = np.argmin(np.abs(self.imp1.t_end - self.bpecg.systime))
        data_ind_hr1 = np.argmin(np.abs(self.imp1.t_tilted + 0 - self.bpecg.hrtime))
        data_ind_hr2 = np.argmin(np.abs(self.imp1.t_end - self.bpecg.hrtime))
        data_ind_pp1 = data_ind_sys1
        data_ind_pp2 = data_ind_sys2
        data_sys = np.divide(self.bpecg.sysfi[data_ind_sys1:data_ind_sys2], baseline_sys)
        data_hr = np.divide(self.bpecg.hr[data_ind_hr1:data_ind_hr2], baseline_hr)
        data_pp = np.divide(self.bpecg.pp[data_ind_pp1:data_ind_pp2], baseline_pp)

        avg_window = 30
        y1 = []
        y2 = []
        current_ind = baseline_ind2
        next_ind = []
        while current_ind <= np.argmin(np.abs(self.imp1.t_end - 0 - avg_window - self.imp1.timestamps)):
            next_ind = np.argmin(np.abs(self.imp1.timestamps - (self.imp1.timestamps[current_ind] + avg_window)))
            y1.append((np.mean(self.imp1_m[current_ind:next_ind])/baseline1-1)*100)
            y2.append((np.mean(self.imp2_m[current_ind:next_ind])/baseline2-1)*100)
            current_ind = next_ind
        x = np.arange(0, len(y1)*avg_window, avg_window)+90
        print(f'The length of x is {len(x)}\n'
              f'The current_ind is {current_ind}\n'
              f'the max_ind is {np.argmin(np.abs(self.imp1.t_end - avg_window - self.imp1.timestamps))}\n'
              f'x max is {max(x)}\n'
              f'EoT is {self.imp1.t_end}\n'
              f'The length of y1 is {len(y1)}\n'
              f'The length of y2 is {len(y2)}')

        x_sys = np.linspace(0, len(y1)*avg_window+90, np.subtract(data_ind_sys2,data_ind_sys1))
        x_hr = np.linspace(0,len(y1)*avg_window+90, np.subtract(data_ind_hr2,data_ind_hr1))
        x_pp = x_sys
        if self.three_channel == True:
            baseline3 = np.mean(self.imp3_m[baseline_ind1:baseline_ind2])
            y1 = []
            y2 = []
            y3 = []
            current_ind = baseline_ind2
            next_ind = []
            while current_ind <= np.argmin(np.abs(self.imp1.t_end - 0 - avg_window - self.imp1.timestamps)):
                next_ind = np.argmin(np.abs(self.imp1.timestamps - (self.imp1.timestamps[current_ind] + avg_window)))
                y1.append((np.mean(self.imp1_m[current_ind:next_ind])/baseline1-1)*100)
                y2.append((np.mean(self.imp2_m[current_ind:next_ind])/baseline2-1)*100)
                y3.append((np.mean(self.imp3_m[current_ind:next_ind]) / baseline3 - 1) * 100)
                current_ind = next_ind
            x = np.arange(0, len(y1) * avg_window, avg_window) + 90
            fig, axs = plt.subplots(nrows=3, ncols=1, sharex='all')
            axs[0].bar(x, y1, width=avg_window)

            axs[0].set_xlabel("Time after tilt (s)")
            axs[0].set_ylabel("Percentage impedance change (%)")
            axs[0].set_xlim(0, max(x))
            axs[0].plot(x_sys, data_sys, color='red', label='SysBP')
            axs[0].plot(x_hr, data_hr, color='green', label='HR')
            axs[0].plot(x_pp, data_pp, color='orange', label='Pulse Pressure')
            axs[0].legend()
            if hasattr(self.imp1, 't_gtn'):
                axs[0].axvline(self.imp1.t_gtn - self.imp1.t_tilted, color='r')
                axs[0].text(self.imp1.t_gtn - self.imp1.t_tilted + 0.1, 0, 'GTN', rotation=90)
                axs[0].set_title("Thoracic Impedance change between tilt+90s and EoT with GTN")
            else:
                axs[0].set_title("Thoracic Impedance change between tilt+90s and EoT No GTN")
            axs[1].bar(x, y2, width=avg_window)
            axs[1].set_title("Splanchnic Impedance change between tilt+90s and EoT")
            axs[1].set_xlabel("Time after tilt (s)")
            axs[1].set_ylabel("Percentage impedance change (%)")
            axs[1].set_xlim(0, max(x))
            axs[1].plot(x_sys, data_sys, color='red', label='SysBP')
            axs[1].plot(x_hr, data_hr, color='green', label='HR')
            axs[1].plot(x_pp, data_pp, color='orange', label='Pulse Pressure')
            axs[1].legend()
            if hasattr(self.imp2, 't_gtn'):
                axs[1].axvline(self.imp2.t_gtn - self.imp2.t_tilted, color='r')
                axs[1].text(self.imp2.t_gtn - self.imp2.t_tilted + 0.1, 0, 'GTN', rotation=90)
                axs[1].set_title("Thoracic Impedance change between tilt+90s and EoT with GTN")
            else:
                axs[1].set_title("Thoracic Impedance change between tilt+90s and EoT No GTN")
            axs[2].bar(x, y3, width=avg_window)
            axs[2].set_title("Thigh Impedance change between tilt+90s and EoT")
            axs[2].set_xlabel("Time after tilt (s)")
            axs[2].set_ylabel("Percentage impedance change (%)")
            axs[2].set_xlim(0, max(x))
            axs[2].plot(x_sys, data_sys, color='red', label='SysBP')
            axs[2].plot(x_hr, data_hr, color='green', label='HR')
            axs[2].plot(x_pp, data_pp, color='orange', label='Pulse Pressure')
            axs[2].legend()
            if hasattr(self.imp3, 't_gtn'):
                axs[2].axvline(self.imp3.t_gtn - self.imp3.t_tilted, color='r')
                axs[2].text(self.imp3.t_gtn - self.imp3.t_tilted + 0.1, 0, 'GTN', rotation=90)
                axs[2].set_title("Thoracic Impedance change between tilt+90s and EoT with GTN")
            else:
                axs[2].set_title("Thoracic Impedance change between tilt+90s and EoT No GTN")

            for i, v in enumerate(y1):
                if v >= 0:
                    axs[0].text(i * avg_window + 90, v + 0.05, str(round(v, 2)) + "%", ha='center', fontsize=7)
                    axs[0].text(i * avg_window + 90, v + 1, str(round(v * baseline1 / 100, 2)), ha='center', fontsize=7)
                if v < 0:
                    axs[0].text(i * avg_window + 90, v - 0.1, str(round(v, 2)) + "%", ha='center', fontsize=7)
                    axs[0].text(i * avg_window + 90, v - 1, str(round(v * baseline2 / 100, 2)), ha='center', fontsize=7)
            for i, v in enumerate(y2):
                if v >= 0:
                    axs[1].text(i * avg_window + 90, v + 0.05, str(round(v, 2)) + "%", ha='center', fontsize=7)
                    axs[1].text(i * avg_window + 90, v + 1, str(round(v * baseline1 / 100, 2)), ha='center', fontsize=7)
                if v < 0:
                    axs[1].text(i * avg_window + 90, v - 0.1, str(round(v, 2)) + "%", ha='center', fontsize=7)
                    axs[1].text(i * avg_window + 90, v + 1, str(round(v * baseline2 / 100, 2)), ha='center', fontsize=7)
            for i, v in enumerate(y3):
                if v >= 0:
                    axs[2].text(i * avg_window + 90, v + 0.05, str(round(v, 2)) + "%", ha='center', fontsize=7)
                    axs[2].text(i * avg_window + 90, v + 1, str(round(v * baseline1 / 100, 2)), ha='center', fontsize=7)
                if v < 0:
                    axs[2].text(i * avg_window + 90, v - 0.1, str(round(v, 2)) + "%", ha='center', fontsize=7)
                    axs[2].text(i * avg_window + 90, v + 1, str(round(v * baseline2 / 100, 2)), ha='center', fontsize=7)
            plt.show()
        else:
            fig, axs = plt.subplots(nrows=2, ncols=1, sharex='all')
            axs[0].bar(x, y1, width=avg_window)

            axs[0].set_xlabel("Time after tilt (s)")
            axs[0].set_ylabel("Percentage impedance change (%)")
            axs[0].set_xlim(0,max(x))
            axs[0].plot(x_sys, data_sys, color = 'red', label = 'SysBP')
            axs[0].plot(x_hr, data_hr, color = 'green', label = 'HR')
            axs[0].plot(x_pp, data_pp, color = 'orange', label = 'Pulse Pressure')
            axs[0].legend()
            if hasattr(self.imp1, 't_gtn'):
                axs[0].axvline(self.imp1.t_gtn - self.imp1.t_tilted, color='r')
                axs[0].text(self.imp1.t_gtn - self.imp1.t_tilted + 0.1, 0, 'GTN', rotation=90)
                axs[0].set_title("Thoracic Impedance change between tilt+90s and EoT with GTN")
            else:
                axs[0].set_title("Thoracic Impedance change between tilt+90s and EoT No GTN")
            axs[1].bar(x, y2, width=avg_window)
            axs[1].set_title("Splanchnic Impedance change between tilt+90s and EoT")
            axs[1].set_xlabel("Time after tilt (s)")
            axs[1].set_ylabel("Percentage impedance change (%)")
            axs[1].set_xlim(0, max(x))
            axs[1].plot(x_sys, data_sys, color='red', label='SysBP')
            axs[1].plot(x_hr, data_hr, color='green', label='HR')
            axs[1].plot(x_pp, data_pp, color='orange', label='Pulse Pressure')
            axs[1].legend()
            if hasattr(self.imp2, 't_gtn'):
                axs[1].axvline(self.imp2.t_gtn - self.imp2.t_tilted, color='r')
                axs[1].text(self.imp2.t_gtn - self.imp2.t_tilted + 0.1, 0, 'GTN', rotation=90)
                axs[1].set_title("Thoracic Impedance change between tilt+90s and EoT with GTN")
            else:
                axs[1].set_title("Thoracic Impedance change between tilt+90s and EoT No GTN")
            for i, v in enumerate(y1):
                if v >= 0:
                    axs[0].text(i * avg_window + 90, v + 0.05, str(round(v, 2)) + "%", ha='center', fontsize=7)
                    axs[0].text(i * avg_window + 90, v + 1, str(round(v * baseline1 / 100, 2)), ha='center', fontsize=7)
                if v < 0:
                    axs[0].text(i * avg_window + 90, v - 0.1, str(round(v, 2)) + "%", ha='center', fontsize=7)
                    axs[0].text(i * avg_window + 90, v - 1, str(round(v * baseline2 / 100, 2)), ha='center', fontsize=7)
            for i, v in enumerate(y2):
                if v >= 0:
                    axs[1].text(i * avg_window + 90, v + 0.05, str(round(v, 2)) + "%", ha='center', fontsize=7)
                    axs[1].text(i * avg_window + 90, v + 1, str(round(v * baseline1 / 100, 2)), ha='center', fontsize=7)
                if v < 0:
                    axs[1].text(i * avg_window + 90, v - 0.1, str(round(v, 2)) + "%", ha='center', fontsize=7)
                    axs[1].text(i * avg_window + 90, v + 1, str(round(v * baseline2 / 100, 2)), ha='center', fontsize=7)
            plt.show()

        baseline_ind1 = np.argmin(np.abs(self.imp1.t_tilted - 30 - self.bpecg.systime))
        baseline_ind2 = np.argmin(np.abs(self.imp1.t_tilted + 0 - self.bpecg.diatime))
        # eot_ind = np.argmin(np.abs(self.imp1.t_end - self.imp1.timestamps))
        baseline1 = np.mean(self.bpecg.sysfi[baseline_ind1:baseline_ind2])
        baseline2 = np.mean(self.bpecg.diafi[baseline_ind1:baseline_ind2])
        avg_window = 10
        # x = np.arange(0, np.floor((np.floor(self.imp1.timestamps[eot_ind])-np.floor(self.imp1.timestamps[baseline_ind2]))), avg_window)
        y1 = []
        y2 = []
        current_ind = baseline_ind2
        next_ind = []
        while current_ind <= np.argmin(np.abs(self.imp1.t_end - avg_window - self.bpecg.systime)):
            next_ind = np.argmin(np.abs(self.bpecg.systime - (self.bpecg.systime[current_ind] + avg_window)))
            y1.append((np.mean(self.bpecg.sysfi[current_ind:next_ind]) / baseline1 - 1) * 100)
            y2.append((np.mean(self.bpecg.diafi[current_ind:next_ind]) / baseline2 - 1) * 100)
            current_ind = next_ind
        x = np.arange(0, len(y1) * avg_window, avg_window) + 90
        print(f'The length of x is {len(x)}\n'
              f'The current_ind is {current_ind}\n'
              f'the max_ind is {np.argmin(np.abs(self.imp1.t_end - avg_window - self.imp1.timestamps))}\n'
              f'x max is {max(x)}\n'
              f'EoT is {self.imp1.t_end}\n'
              f'The length of y1 is {len(y1)}\n'
              f'The length of y2 is {len(y2)}')
        fig, axs = plt.subplots(nrows=2, ncols=1, sharex='all')
        axs[0].bar(x, y1, width=avg_window)
        axs[0].set_title("SBP change between tilt+90s and EoT")
        axs[0].set_xlabel("Time after tilt (s)")
        axs[0].set_ylabel("Percentage impedance change (%)")
        axs[0].set_xlim(min(x), max(x))
        axs[1].bar(x, y2, width=avg_window)
        axs[1].set_title("DBP change between tilt+90s and EoT")
        axs[1].set_xlabel("Time after tilt (s)")
        axs[1].set_ylabel("Percentage impedance change (%)")
        axs[1].set_xlim(min(x), max(x))
        for i, v in enumerate(y1):
            if v >= 0:
                axs[0].text(i * avg_window + 90, v + 0.05, str(round(v, 2)) + "%", ha='center', fontsize=7)
                axs[0].text(i * avg_window + 90, v + 3, str(round(v * baseline1 / 100, 2)), ha='center', fontsize=7)
            if v < 0:
                axs[0].text(i * avg_window + 90, v - 0.1, str(round(v, 2)) + "%", ha='center', fontsize=7)
                axs[0].text(i * avg_window + 90, v - 3, str(round(v * baseline2 / 100, 2)), ha='center', fontsize=7)
        for i, v in enumerate(y2):
            if v >= 0:
                axs[1].text(i * avg_window + 90, v + 0.05, str(round(v, 2)) + "%", ha='center', fontsize=7)
                axs[1].text(i * avg_window + 90, v + 3, str(round(v * baseline1 / 100, 2)), ha='center', fontsize=7)
            if v < 0:
                axs[1].text(i * avg_window + 90, v - 0.1, str(round(v, 2)) + "%", ha='center', fontsize=7)
                axs[1].text(i * avg_window + 90, v + 3, str(round(v * baseline2 / 100, 2)), ha='center', fontsize=7)
        plt.show()

    def select6(self):
        print("select 6 button pushed")

        # New code
        # self.select6_region_items = []
        # for plot in [self.plot3,self.plot2,self.plot4,self.plot5,self.plot6]:
        #     self.select6_region_item = pg.LinearRegionItem([0, 6])
        #     plot.addItem(self.select6_region_item)
        #     self.select6_region_items.append(self.select6_region_item)
        #     self.select6_region_item.sigRegionChanged.connect(self.update6_region)

        self.Average_window_length = 6 # Change this number to alter the length of the average window

        # New code

        self.select6_1 = pg.LinearRegionItem([0, self.Average_window_length])
        self.select6_2 = pg.LinearRegionItem([0, self.Average_window_length])
        self.select6_3 = pg.LinearRegionItem([0, self.Average_window_length])
        self.select6_4 = pg.LinearRegionItem([0, self.Average_window_length])
        self.select6_5 = pg.LinearRegionItem([0, self.Average_window_length])

        self.plot3.addItem(self.select6_1)
        self.plot4.addItem((self.select6_2))
        self.plot2.addItem(self.select6_3)
        self.plot5.addItem(self.select6_4)
        self.plot6.addItem(self.select6_5)
        self.select6_1.sigRegionChanged.connect(self.update6_region)
        self.select6_2.sigRegionChanged.connect(self.update6_region2)
        self.select6_3.sigRegionChanged.connect(self.update6_region3)
        self.select6_4.sigRegionChanged.connect(self.update6_region4)
        self.select6_5.sigRegionChanged.connect(self.update6_region5)
        if self.three_channel == True:
            self.select6_6 = pg.LinearRegionItem([0, self.Average_window_length])
            self.plot7.addItem(self.select6_6)
            self.select6_6.sigRegionChanged.connect(self.update6_region6)

        # self.timer = QtCore.QTimer(self)
        # self.timer.timeout.connect(self.update_region())
        # self.timer.start(100)

    def update6_region(self):
        self.xmin6, self.xmax6 = self.select6_1.getRegion()
        self.select6_1.setRegion((self.xmin6, self.xmin6 + self.Average_window_length))
        # for select6_regions in self.select6_1:
        #     select6_regions.setRegion(self.self.select6_1.getRegion())
        # print(self.xmin6)
        # print(self.xmax6)
        imp1min6_ind = np.argmin(np.abs(self.xmin6 - self.imp1.timestamps))
        imp1max6_ind = np.argmin(np.abs(self.xmax6 - self.imp1.timestamps))
        imp2min6_ind = np.argmin(np.abs(self.xmin6 - self.imp2.timestamps))
        imp2max6_ind = np.argmin(np.abs(self.xmax6 - self.imp2.timestamps))
        self.bpecg.maptime=np.array(self.bpecg.maptime)
        self.bpecg.hrtime=np.array(self.bpecg.hrtime)
        self.bpecg.aptime=np.array(self.bpecg.aptime)
        self.bpecg.systime=np.array(self.bpecg.systime)
        self.bpecg.diatime=np.array(self.bpecg.diatime)
        mapmin6_ind = np.argmin(np.abs(self.xmin6 - self.bpecg.maptime))
        mapmax6_ind = np.argmin(np.abs(self.xmax6 - self.bpecg.maptime))
        hrmin6_ind = np.argmin(np.abs(self.xmin6 - self.bpecg.hrtime))
        hrmax6_ind = np.argmin(np.abs(self.xmax6 - self.bpecg.hrtime))
        apmin6_ind = np.argmin(np.abs(self.xmin6 - self.bpecg.aptime))
        apmax6_ind = np.argmin(np.abs(self.xmax6 - self.bpecg.aptime))
        sysmin6_ind = np.argmin(np.abs(self.xmin6 - self.bpecg.systime))
        sysmax6_ind = np.argmin(np.abs(self.xmax6 - self.bpecg.systime))
        diamin6_ind = np.argmin(np.abs(self.xmin6 - self.bpecg.diatime))
        diamax6_ind = np.argmin(np.abs(self.xmax6 - self.bpecg.diatime))
        imp1avg6 = np.mean(self.imp1_m[imp1min6_ind:imp1max6_ind + 1])
        imp1min6 = np.min(self.imp1_m[imp1min6_ind:imp1max6_ind + 1])
        imp1max6 = np.max(self.imp1_m[imp1min6_ind:imp1max6_ind + 1])
        imp2avg6 = np.mean(self.imp2_m[imp2min6_ind:imp2max6_ind + 1])
        imp2max6 = np.max(self.imp2_m[imp2min6_ind:imp2max6_ind + 1])
        imp2min6 = np.min(self.imp2_m[imp2min6_ind:imp2max6_ind + 1])
        mapavg6 = np.mean(self.bpecg.mapfi[mapmin6_ind:mapmax6_ind + 1])
        hravg6 = np.mean(self.bpecg.mapfi[hrmin6_ind:hrmax6_ind + 1])
        hrmin6 = np.min(self.bpecg.mapfi[hrmin6_ind:hrmax6_ind + 1])
        hrmax6 = np.max(self.bpecg.mapfi[hrmin6_ind:hrmax6_ind + 1])
        apavg6 = np.mean(self.bpecg.ap[apmin6_ind:apmax6_ind + 1])
        sysavg6 = np.mean(self.bpecg.sysfi[sysmin6_ind:sysmax6_ind + 1])
        for sysbp in [self.bpecg.sysfi[sysmin6_ind:sysmax6_ind + 1]]:
            print(sysbp)
        for sysbp in [self.bpecg.systime[sysmin6_ind:sysmax6_ind + 1]]:
            print(sysbp)
        print(f'{sysmin6_ind} {sysmax6_ind}')
        print(self.bpecg.sysfi[1:10])
        sysmin6 = np.min(self.bpecg.sysfi[sysmin6_ind:sysmax6_ind + 1])
        sysmax6 = np.max(self.bpecg.sysfi[sysmin6_ind:sysmax6_ind + 1])
        diaavg6 = np.mean(self.bpecg.diafi[diamin6_ind:diamax6_ind + 1])
        diamin6 = np.min(self.bpecg.diafi[diamin6_ind:diamax6_ind + 1])
        diamax6 = np.max(self.bpecg.diafi[diamin6_ind:diamax6_ind + 1])
        #pulsemin6 = np.min()
        if self.three_channel == True:
            imp3min6_ind = np.argmin(np.abs(self.xmin6 - self.imp3.timestamps))
            imp3max6_ind = np.argmin(np.abs(self.xmax6 - self.imp3.timestamps))
            imp3avg6 = np.mean(self.imp3_m[imp3min6_ind:imp3max6_ind + 1])
            imp3max6 = np.max(self.imp3_m[imp3min6_ind:imp3max6_ind + 1])
            imp3min6 = np.min(self.imp3_m[imp3min6_ind:imp3max6_ind + 1])
            self.imp1avg6label.setText(
                f'Average within {round(self.xmin6, 2)}s and {round(self.xmax6, 2)}s\nThoracic Impedance is {round(imp1avg6, 2)},[{round(imp1min6, 2)},{round(imp1max6, 2)}]'
                f'\nAVG Splanchnic Impedance is {round(imp2avg6, 2)},[{round(imp2min6, 2)},{round(imp2max6, 2)}]'
                f'\nAVG Thigh Impedance is {round(imp3avg6,2)},[{round(imp3min6,2)},{round(imp3max6,2)}]'
                f'\nHeart Rate is {round(hravg6, 2)},[{round(hrmin6, 2)},{round(hrmax6, 2)}]'
                f'\nSystolic Blood pressure is {round(sysavg6, 2)},[{round(sysmin6, 2)},{round(sysmax6, 2)}]'
                f'\nDiastolic Blood Pressure is {round(diaavg6, 2)},[{round(diamin6, 2)},{round(diamax6, 2)}]'
                f'\nPulse Pressure is {round(sysavg6 - diaavg6, 2)}mmHg'
                f'\nMAP is {round(mapavg6, 2)}mmHg')
        else:
            self.imp1avg6label.setText(f'Average within {round(self.xmin6,2)}s and {round(self.xmax6,2)}s\nThoracic Impedance is {round(imp1avg6,2)},[{round(imp1min6,2)},{round(imp1max6,2)}]'
                                       f'\nAVG Splanchnic Impedance is {round(imp2avg6,2)},[{round(imp2min6,2)},{round(imp2max6,2)}]'
                                       f'\nHeart Rate is {round(hravg6,2)},[{round(hrmin6,2)},{round(hrmax6,2)}]'
                                       f'\nSystolic Blood pressure is {round(sysavg6,2)},[{round(sysmin6,2)},{round(sysmax6,2)}]'
                                       f'\nDiastolic Blood Pressure is {round(diaavg6,2)},[{round(diamin6,2)},{round(diamax6,2)}]'
                                       f'\nPulse Pressure is {round(sysavg6-diaavg6,2)}mmHg'
                                       f'\nMAP is {round(mapavg6,2)}mmHg')

    def update6_region2(self):
        self.select6_2.setRegion(self.select6_1.getRegion())

    def update6_region3(self):
        self.select6_3.setRegion(self.select6_1.getRegion())

    def update6_region4(self):
        self.select6_4.setRegion(self.select6_1.getRegion())

    def update6_region5(self):
        self.select6_5.setRegion(self.select6_1.getRegion())

    def update6_region6(self):
        self.select6_6.setRegion(self.select6_1.getRegion())

    def selectR(self):
        print("select R button pushed")

        self.selectR_1 = pg.LinearRegionItem([0, 6])
        self.selectR_2 = pg.LinearRegionItem([0, 6])
        self.selectR_3 = pg.LinearRegionItem([0, 6])
        self.selectR_4 = pg.LinearRegionItem([0, 6])
        self.selectR_5 = pg.LinearRegionItem([0, 6])

        try:


            # for plot in [self.plot3,self.plot2,self.plot4,self.plot5]:
            #     plot_items = plot.plotItem.listDataItems()
            #     for item in plot_items:
            #         print(item.name())
            #     plot.removeItem(self.select6_region_item)
            self.imp1avg6label.setText("")
            self.plot2.removeItem(self.select6_3)
            self.plot3.removeItem(self.select6_1)
            self.plot4.removeItem(self.select6_2)
            self.plot5.removeItem(self.select6_4)
            self.plot6.removeItem(self.select6_5)
        except:
            pass

        self.plot3.addItem(self.selectR_1)
        self.plot4.addItem(self.selectR_2)
        self.plot2.addItem(self.selectR_3)
        self.plot5.addItem(self.selectR_4)
        self.plot6.addItem(self.selectR_5)
        self.selectR_1.sigRegionChanged.connect(self.updateR_region)
        self.selectR_2.sigRegionChanged.connect(self.updateR_region2)
        self.selectR_3.sigRegionChanged.connect(self.updateR_region3)
        self.selectR_4.sigRegionChanged.connect(self.updateR_region4)
        self.selectR_5.sigRegionChanged.connect(self.updateR_region5)

        if self.three_channel == True:
            self.selectR_6 = pg.LinearRegionItem([0, 6])
            try:
                self.plot7.removeItem(self.select6_6)
            except:
                pass
            self.plot7.addItem(self.selectR_6)
            self.selectR_6.sigRegionChanged.connect(self.updateR_region6)

    def updateR_region(self):
        self.xminR, self.xmaxR = self.selectR_1.getRegion()
        print(self.xminR)
        print(self.xmaxR)

    def updateR_region2(self):
        self.selectR_2.setRegion(self.selectR_1.getRegion())

    def updateR_region3(self):
        self.selectR_3.setRegion(self.selectR_1.getRegion())

    def updateR_region4(self):
        self.selectR_4.setRegion(self.selectR_1.getRegion())

    def updateR_region5(self):
        self.selectR_5.setRegion(self.selectR_1.getRegion())

    def updateR_region6(self):
        self.selectR_6.setRegion(self.selectR_1.getRegion())

    def selectI(self):
        try:
            self.plot2.removeItem(self.selectR_3)
            self.plot3.removeItem(self.selectR_1)
            self.plot4.removeItem(self.selectR_2)
            self.plot5.removeItem(self.selectR_4)
            self.plot6.removeItem(self.selectR_5)
        except:
            pass
        self.vline_items = []
        for plot in [self.plot3,self.plot2,self.plot4,self.plot5,self.plot6]:
            vline_item = pg.LinearRegionItem([0, 30])
            plot.addItem(vline_item)
            self.vline_items.append(vline_item)
            vline_item.sigRegionChanged.connect(self.update_vlines)
        if self.three_channel == True:
            try:
                self.plot7.removeItem(self.selectR_6)
            except:
                pass
            vline_item = pg.LinearRegionItem([0 , 30])
            self.plot7.addItem(vline_item)
            self.vline_items.append(vline_item)
            vline_item.sigRegionChanged.connect(self.update_vlines)

    def update_vlines(self):
        # self.xPos = self.vline_items[0].value()
        self.xminI, self.xmaxI = self.vline_items[0].getRegion()
        # print(f'xminI is {self.xminI}, xmaxI is {self.xmaxI}')
        imp1minR_ind = np.argmin(np.abs(self.xminR - self.imp1.timestamps))
        imp1maxR_ind = np.argmin(np.abs(self.xmaxR - self.imp1.timestamps))
        imp2minR_ind = np.argmin(np.abs(self.xminR - self.imp2.timestamps))
        imp2maxR_ind = np.argmin(np.abs(self.xmaxR - self.imp2.timestamps))
        self.bpecg.maptime = np.array(self.bpecg.maptime)
        self.bpecg.hrtime = np.array(self.bpecg.hrtime)
        self.bpecg.aptime = np.array(self.bpecg.aptime)
        self.bpecg.systime = np.array(self.bpecg.systime)
        self.bpecg.diatime = np.array(self.bpecg.diatime)
        mapminR_ind = np.argmin(np.abs(self.xminR - self.bpecg.maptime))
        mapmaxR_ind = np.argmin(np.abs(self.xmaxR - self.bpecg.maptime))
        hrminR_ind = np.argmin(np.abs(self.xminR - self.bpecg.hrtime))
        hrmaxR_ind = np.argmin(np.abs(self.xmaxR - self.bpecg.hrtime))
        apminR_ind = np.argmin(np.abs(self.xminR - self.bpecg.aptime))
        apmaxR_ind = np.argmin(np.abs(self.xmaxR - self.bpecg.aptime))
        sysminR_ind = np.argmin(np.abs(self.xminR - self.bpecg.systime))
        sysmaxR_ind = np.argmin(np.abs(self.xmaxR - self.bpecg.systime))
        diaminR_ind = np.argmin(np.abs(self.xminR - self.bpecg.diatime))
        diamaxR_ind = np.argmin(np.abs(self.xminR - self.bpecg.diatime))
        imp1avgR = np.nanmean(self.imp1_m[imp1minR_ind:imp1maxR_ind + 1])
        imp2avgR = np.nanmean(self.imp2_m[imp2minR_ind:imp2maxR_ind + 1])
        mapavgR = np.nanmean(self.bpecg.mapfi[mapminR_ind:mapmaxR_ind + 1])
        hravgR = np.nanmean(self.bpecg.mapfi[hrminR_ind:hrmaxR_ind + 1])
        apavgR = np.nanmean(self.bpecg.ap[apminR_ind:apmaxR_ind + 1])
        sysavgR = np.mean(self.bpecg.sysfi[sysminR_ind:sysmaxR_ind + 1])
        diaavgR = np.mean(self.bpecg.diafi[diaminR_ind:diamaxR_ind + 1])
        imp1minI_ind = np.argmin(np.abs(self.xminI - self.imp1.timestamps))
        imp1maxI_ind = np.argmin(np.abs(self.xmaxI - self.imp1.timestamps))
        imp1avgI = np.nanmean(self.imp1_m[imp1minI_ind:imp1maxI_ind + 1])
        imp2minI_ind = np.argmin(np.abs(self.xminI - self.imp2.timestamps))
        imp2maxI_ind = np.argmin(np.abs(self.xmaxI - self.imp2.timestamps))
        imp2avgI = np.nanmean(self.imp2_m[imp2minI_ind:imp2maxI_ind + 1])
        mapminI_ind = np.argmin(np.abs(self.xminI - self.bpecg.maptime))
        mapmaxI_ind = np.argmin(np.abs(self.xmaxI - self.bpecg.maptime))
        mapavgI = np.nanmean(self.bpecg.mapfi[mapminI_ind:mapmaxI_ind + 1])
        hrminI_ind = np.argmin(np.abs(self.xminI - self.bpecg.hrtime))
        hrmaxI_ind = np.argmin(np.abs(self.xmaxI - self.bpecg.hrtime))
        hravgI = np.nanmean(self.bpecg.mapfi[hrminI_ind:hrmaxI_ind + 1])
        sysminI_ind = np.argmin(np.abs(self.xminI - self.bpecg.systime))
        sysmaxI_ind = np.argmin(np.abs(self.xmaxI - self.bpecg.systime))
        sysavgI = np.nanmean(self.bpecg.sysfi[sysminI_ind:sysmaxI_ind + 1])
        diaminI_ind = np.argmin(np.abs(self.xminI - self.bpecg.diatime))
        diamaxI_ind = np.argmin(np.abs(self.xmaxI - self.bpecg.diatime))
        diaavgI = np.nanmean(self.bpecg.diafi[diaminI_ind:diamaxI_ind + 1])
        # apI_ind = np.argmin(np.abs(self.xPos - self.bpecg.aptime))
        imp1diff = imp1avgI / imp1avgR * 100 -100
        imp2diff = imp2avgI / imp2avgR * 100 -100
        mapdiff = mapavgI / mapavgR * 100 -100
        hrdiff = hravgI / hravgR * 100 -100
        sysdiff = sysavgI / sysavgR *100 -100
        diadiff = diaavgI / diaavgR *100 -100
        # apdiff = self.bpecg.ap[apI_ind] / apavgR * 100 -100
        if self.three_channel ==True:
            imp3minR_ind = np.argmin(np.abs(self.xminR - self.imp3.timestamps))
            imp3maxR_ind = np.argmin(np.abs(self.xmaxR - self.imp3.timestamps))
            imp3avgR = np.nanmean(self.imp3_m[imp3minR_ind:imp3maxR_ind + 1])
            imp3minI_ind = np.argmin(np.abs(self.xminI - self.imp3.timestamps))
            imp3maxI_ind = np.argmin(np.abs(self.xmaxI - self.imp3.timestamps))
            imp3avgI = np.nanmean(self.imp3_m[imp3minI_ind:imp3maxI_ind + 1])
            imp3diff = imp3avgI / imp3avgR * 100 - 100
            self.relative_change_label.setText(
                f'The baseline data is between {round(self.xminR, 2)} and {round(self.xmaxR, 2)}'
                f'\nThe current data region for relative change calculation is [{round(self.xminI, 2)},{round(self.xmaxI, 2)}]'
                f'\nThoracic Impedance change is {round(imp1avgI - imp1avgR, 2)},  {round(imp1diff, 2)}%'
                f'\nSplanchnic Impedance change is {round(imp2avgI - imp2avgR, 2)}, {round(imp2diff, 2)}%'
                f'\nThigh Impedance change is {round(imp3avgI - imp3avgR,2)},{round(imp3diff,2)}%'
                f'\nHeart Rate change is {round(hravgI - hravgR, 2)}, {round(hrdiff, 2)}%'
                f'\nSBP change is {round(sysavgI - sysavgR, 2)}, {round(sysdiff, 2)}%'
                f'\nDBP change is {round(diaavgI - diaavgR, 2)}, {round(diadiff, 2)}%'
                f'\nMAP change is {round(mapavgI - mapavgR, 2)}, {round(mapdiff, 2)}%'
            )

        else:
            self.relative_change_label.setText(
                f'The baseline data is between {round(self.xminR, 2)} and {round(self.xmaxR, 2)}'
                f'\nThe current data region for relative change calculation is [{round(self.xminI,2)},{round(self.xmaxI,2)}]'
                f'\nThoracic Impedance change is {round(imp1avgI - imp1avgR, 2)},  {round(imp1diff, 2)}%'
                f'\nSplanchnic Impedance change is {round(imp2avgI - imp2avgR, 2)}, {round(imp2diff, 2)}%'
                f'\nHeart Rate change is {round(hravgI - hravgR, 2)}, {round(hrdiff, 2)}%'
                f'\nSBP change is {round(sysavgI - sysavgR, 2)}, {round(sysdiff, 2)}%'
                f'\nDBP change is {round(diaavgI - diaavgR, 2)}, {round(diadiff, 2)}%'
                f'\nMAP change is {round(mapavgI - mapavgR, 2)}, {round(mapdiff, 2)}%'
            )
        for vline_item in self.vline_items:
            vline_item.setRegion(self.vline_items[0].getRegion())

    def imp_analysis(self):
        freqwanted = 50000
        input_freq = float(freqwanted)
        imp1_freq_idx = np.argmin(np.abs(self.imp1.freq - input_freq))
        imp2_freq_idx = np.argmin(np.abs(self.imp2.freq - input_freq))

        AvgAbsImp1 = self.imp1.abs_ohm_np[:, imp1_freq_idx]
        AvgAbsImp2 = self.imp2.abs_ohm_np[:, imp2_freq_idx]

        ZImp1 = stats.zscore(AvgAbsImp1)
        ZImp2 = stats.zscore(AvgAbsImp2)
        threshold = 3
        outlier1 = np.concatenate(np.where(ZImp1 > threshold))
        outlier2 = np.concatenate(np.where(ZImp2 > threshold))
        AvgAbsImp1NoOL = AvgAbsImp1
        AvgAbsImp2NoOL = AvgAbsImp2
        for ind in outlier1:
            if 1 <= ind < len(AvgAbsImp1NoOL) - 1:
                AvgAbsImp1NoOL[ind] = np.mean(np.array(AvgAbsImp1NoOL[ind - 1], AvgAbsImp1NoOL[ind + 1]))
            elif ind == 0:
                AvgAbsImp1NoOL[ind] = AvgAbsImp1NoOL[ind + 1]
            else:
                AvgAbsImp1NoOL[ind] = AvgAbsImp1NoOL[ind - 1]
        for ind in outlier2:
            if 1 <= ind < len(AvgAbsImp2NoOL) - 1:
                AvgAbsImp2NoOL[ind] = np.mean(np.array(AvgAbsImp2NoOL[ind - 1], AvgAbsImp2NoOL[ind + 1]))
            elif ind == 0:
                AvgAbsImp2NoOL[ind] = AvgAbsImp2NoOL[ind + 1]
            else:
                AvgAbsImp2NoOL[ind] = AvgAbsImp2NoOL[ind - 1]

        fs1 = self.imp1.filenum / (self.imp1.timestamps[-1] - self.imp1.timestamps[0])
        fs2 = self.imp2.filenum / (self.imp2.timestamps[-1] - self.imp2.timestamps[0])
        self.imp1_m=AvgAbsImp1NoOL
        self.imp2_m=AvgAbsImp2NoOL
        if self.three_channel == True:
            imp3_freq_idx = np.argmin(np.abs(self.imp3.freq - input_freq))
            AvgAbsImp3 = self.imp3.abs_ohm_np[:, imp3_freq_idx]
            ZImp3 = stats.zscore(AvgAbsImp2)
            outlier3 = np.concatenate(np.where(ZImp3 > threshold))
            AvgAbsImp3NoOL = AvgAbsImp3
            for ind in outlier3:
                if 1 <= ind < len(AvgAbsImp3NoOL) - 1:
                    AvgAbsImp3NoOL[ind] = np.mean(np.array(AvgAbsImp3NoOL[ind - 1], AvgAbsImp3NoOL[ind + 1]))
                elif ind == 0:
                    AvgAbsImp3NoOL[ind] = AvgAbsImp3NoOL[ind + 1]
                else:
                    AvgAbsImp3NoOL[ind] = AvgAbsImp3NoOL[ind - 1]
            fs3 = self.imp3.filenum / (self.imp3.timestamps[-1] - self.imp3.timestamps[0])
            self.imp3_m = AvgAbsImp3NoOL

    def update_plot2(self):
        # Get the selected region
        xmin, xmax = self.selection_region.getRegion()

        # Update the second plot with the selected region
        #self.plot2.clear()
        x = self.bpecg.maptime
        y = self.bpecg.mapfi
        self.plot2.plot(x, y)
        self.plot2.setTitle('MAP')
        # Set the range of the second plot to the selected region
        for plot in [self.plot2, self.plot3, self.plot4, self.plot5, self.plot6]:
            plot.setXRange(xmin, xmax)
            plot.setLimits(xMin=xmin, xMax=xmax)
        if self.three_channel == True:
            self.plot7.setXRange(xmin, xmax)
            self.plot7.setLimits(xMin=xmin, xMax=xmax)
        print(xmin)
        print(xmax)


#@cl_app.default
def main(data_dir: Path):
    app = QtWidgets.QApplication([])
    window = Startup(data_dir=data_dir)
    window.show()
    app.exec()


if __name__ == '__main__':
    main(data_dir="/Volumes/Matt-Temp/impedance_data")
