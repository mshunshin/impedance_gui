import sys
import os
from PySide6 import QtWidgets, QtGui, QtCore
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QSplitter, QLabel
from imp.reader import Sciospec
from imp.bpecg import Nova
from pathlib import Path
from scipy import stats
import pyqtgraph as pg
import numpy as np
import matplotlib.pyplot as plt


class Startup(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.region_item = pg.LinearRegionItem()

        # Create a QPushButton object and set its properties
        self.setWindowTitle("Welcome to use Impedance Analysis GUI")
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
        contains_string = "Patient"

        folders = [folder for folder in os.listdir(self.selected_directory) if
                   contains_string in folder and os.path.isdir(os.path.join(self.selected_directory, folder))]
        fig, axs = plt.subplots(nrows=2, ncols=1, sharex='all')
        c = 0
        for folder_name in folders:

            folder = os.path.join(self.selected_directory, folder_name)
            print(f"Processing folder: {folder}")
            GROUP_1 = 'EXT2 1 2 5 6'
            GROUP_2 = 'EXT2 9 10 13 14'
            data_folder_1 = Path(folder) / 'setup_00001' / GROUP_1
            data_folder_2 = Path(folder) / 'setup_00001' / GROUP_2

            self.imp1 = Sciospec(data_folder_1, 1)
            self.imp2 = Sciospec(data_folder_2, 2)
            if self.imp1.freq.all() != 0 and self.imp2.freq.all() != 0:
                print("import imp successfully")

            self.imp_analysis()

            ref_min = np.argmin(np.abs(self.imp1.timestamps - (self.imp1.t_tilted - 180)))
            ref_max = np.argmin(np.abs(self.imp1.timestamps - self.imp1.t_tilted))
            # print(f't_tilt is {self.imp1.t_tilted}\nref_min is {ref_min}\nref_max is {ref_max} min '
            #       f'is {self.imp1.timestamps[ref_min]}\nThe other is {self.imp1.timestamps[ref_max]}')
            baseline1 = np.mean(self.imp1_m[ref_min:ref_max])
            # print(baseline1)
            baseline2 = np.mean(self.imp2_m[ref_min:ref_max])
            after5 = np.argmin(np.abs(self.imp1.timestamps - (self.imp1.t_tilted + 300)))
            x = self.imp1.timestamps[ref_max:after5] - self.imp1.timestamps[ref_max]
            axs[0].plot(x, (self.imp1_m[ref_max:after5] / baseline1 - 1) * 100)
            axs[0].set_title(f'Overlapping thoracic impedance % change after tilt')
            axs[1].plot(x, (self.imp2_m[ref_max:after5] / baseline2 - 1) * 100)
            axs[1].set_title(f'Overlapping splanchnic impedance % change after tilt')
            axs[0].set_ylabel('Percentage %')
            axs[1].set_ylabel('Percentage %')
            c = c + 1
        os.chdir(self.selected_directory)
        fig.set_size_inches(w=25, h=15)
        fig.savefig(f'figure.png', format='png', dpi=1200)
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
        self.imp1_m = AvgAbsImp1NoOL
        self.imp2_m = AvgAbsImp2NoOL


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
        self.bpecg = Nova(folder)
        if self.bpecg.diafi != 0:
            print("import bpecg successfully")
        GROUP_1 = 'EXT2 1 2 5 6'

        GROUP_2 = 'EXT2 9 10 13 14'

        data_folder_1 = Path(folder) / 'setup_00001' / GROUP_1
        data_folder_2 = Path(folder) / 'setup_00001' / GROUP_2

        self.imp1 = Sciospec(data_folder_1, 1)
        self.imp2 = Sciospec(data_folder_2, 2)
        if self.imp1.freq.all() != 0 and self.imp2.freq.all() != 0:
            print("import imp successfully")

        self.imp_analysis()
        self.ref_freq()
        mean1_1, std1_1 = np.mean(self.imp1_m), np.std(self.imp1_m)
        mean1_2, std1_2 = np.mean(self.imp2_m), np.std(self.imp2_m)
        mean2_1, std2_1 = np.mean(self.imp1_ref), np.std(self.imp1_ref)
        mean2_2, std2_2 = np.mean(self.imp2_ref), np.std(self.imp2_ref)
        imp1_1_norm = (self.imp1_m - mean1_1) / std1_1
        imp1_2_norm = (self.imp2_m - mean1_2) / std1_2
        imp2_1_norm = (self.imp1_ref - mean2_1) / std2_1
        imp2_2_norm = (self.imp2_ref - mean2_2) / std2_2
        self.substracted_1 = imp1_1_norm - imp2_1_norm
        self.substracted_2 = imp2_1_norm - imp2_2_norm
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        self.plot1 = pg.PlotWidget()
        self.plot2 = pg.PlotWidget()
        self.plot3 = pg.PlotWidget()
        self.plot4 = pg.PlotWidget()
        self.plot5 = pg.PlotWidget()
        self.plot6 = pg.PlotWidget()

        for plot in [self.plot1, self.plot2, self.plot3, self.plot4, self.plot5, self.plot6]:
            v_tilt = pg.InfiniteLine(pos=self.imp1.t_tilted, angle=90, movable=False)
            plot.addItem(v_tilt)
            label = pg.TextItem(text="Tilt")
            diff = [x - self.imp1.t_tilted for x in self.bpecg.maptime]
            time_index = np.argmin(np.abs(diff))
            label.setPos(self.imp1.t_tilted, self.bpecg.mapfi[time_index])
            plot.addItem(label)
        if hasattr(self.imp1, 't_gtn'):
            for plot in [self.plot1, self.plot2, self.plot3, self.plot4, self.plot5, self.plot6]:
                v_gtn = pg.InfiniteLine(pos=self.imp1.t_gtn, angle=90, movable=False)
                plot.addItem(v_gtn)
                label = pg.TextItem(text="GTN")
                diff = [x - self.imp1.t_gtn for x in self.bpecg.maptime]
                time_index = np.argmin(np.abs(diff))
                label.setPos(self.imp1.t_gtn, self.bpecg.mapfi[time_index])
                plot.addItem(label)
        for plot in [self.plot1, self.plot2, self.plot3, self.plot4, self.plot5, self.plot6]:
            v_end = pg.InfiniteLine(pos=self.imp1.t_end, angle=90, movable=False)
            plot.addItem(v_end)
            label = pg.TextItem(text="EoT")
            diff = [x - self.imp1.t_end for x in self.bpecg.maptime]
            time_index = np.argmin(np.abs(diff))
            label.setPos(self.imp1.t_end, self.bpecg.mapfi[time_index])
            plot.addItem(label)
        self.plot1.plot(self.bpecg.maptime, self.bpecg.mapfi)
        plot_layout.addWidget(self.plot1)
        self.plot1.setFixedHeight(self.height() * 0.1)
        self.plot2.setTitle('MAP')
        self.plot3.plot(self.imp1.timestamps, self.imp1_m)
        self.plot3.setYRange(min(self.imp1_m), max(self.imp1_m))
        self.plot4.plot(self.imp2.timestamps, self.imp2_m)
        self.plot4.setYRange(min(self.imp2_m), max(self.imp2_m))
        self.plot5.plot(self.bpecg.hrtime, self.bpecg.hr)
        self.plot6.plot(self.bpecg.aptime, self.bpecg.ap)
        # self.plot3.setXLink(self.plot2)
        self.plot3.setTitle('Thoracic Impedance')
        # self.plot4.setXLink(self.plot2)
        self.plot4.setTitle('Splanchnic Impedance')
        # self.plot5.setXLink(self.plot2)
        self.plot5.setTitle('Heart Rate')
        self.plot6.setTitle('Beat-Beat Blood Pressure')
        plot_layout.addWidget(self.plot3)
        plot_layout.addWidget(self.plot4)
        plot_layout.addWidget(self.plot5)
        plot_layout.addWidget(self.plot6)
        plot_layout.addWidget(self.plot2)

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
        bottom_panel.setFixedHeight(self.height() * 0.1)
        left_layout.addWidget(bottom_panel)

        # Add the left and right widgets to the splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(plot_widget)

        # Set the initial sizes of the widgets
        splitter.setSizes([self.width() * 0.1, self.width() * 0.9])

        # Set the splitter as the central widget of the main window
        layout.addWidget(splitter)

    def barchart(self):
        baseline_ind1 = np.argmin(np.abs(self.imp1.t_tilted + 30 - self.imp1.timestamps))
        baseline_ind2 = np.argmin(np.abs(self.imp1.t_tilted + 90 - self.imp1.timestamps))
        # eot_ind = np.argmin(np.abs(self.imp1.t_end - self.imp1.timestamps))
        baseline1 = np.mean(self.imp1_m[baseline_ind1:baseline_ind2])
        baseline2 = np.mean(self.imp2_m[baseline_ind1:baseline_ind2])
        avg_window = 20
        # x = np.arange(0, np.floor((np.floor(self.imp1.timestamps[eot_ind])-np.floor(self.imp1.timestamps[baseline_ind2]))), avg_window)
        y1 = []
        y2 = []
        current_ind = baseline_ind2
        next_ind = []
        while current_ind <= np.argmin(np.abs(self.imp1.t_end - avg_window - self.imp1.timestamps)):
            next_ind = np.argmin(np.abs(self.imp1.timestamps - (self.imp1.timestamps[current_ind] + avg_window)))
            y1.append((np.mean(self.imp1_m[current_ind:next_ind]) / baseline1 - 1) * 100)
            y2.append((np.mean(self.imp2_m[current_ind:next_ind]) / baseline2 - 1) * 100)
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
        axs[0].set_title("Thoracic Impedance change between tilt+90s and EoT")
        axs[0].set_xlabel("Time after tilt (s)")
        axs[0].set_ylabel("Percentage impedance change (%)")
        axs[0].set_xlim(min(x), max(x))
        axs[1].bar(x, y2, width=avg_window)
        axs[1].set_title("Splanchnic Impedance change between tilt+90s and EoT")
        axs[1].set_xlabel("Time after tilt (s)")
        axs[1].set_ylabel("Percentage impedance change (%)")
        axs[1].set_xlim(min(x), max(x))
        for i, v in enumerate(y1):
            if v >= 0:
                axs[0].text(i * avg_window + 90, v + 0.05, str(round(v, 2)) + "%", ha='center', fontsize=7)
            if v < 0:
                axs[0].text(i * avg_window + 90, v - 0.1, str(round(v, 2)) + "%", ha='center', fontsize=7)
        for i, v in enumerate(y2):
            if v >= 0:
                axs[1].text(i * avg_window + 90, v + 0.05, str(round(v, 2)) + "%", ha='center', fontsize=7)
            if v < 0:
                axs[1].text(i * avg_window + 90, v - 0.1, str(round(v, 2)) + "%", ha='center', fontsize=7)
        plt.show()



        baseline_ind1 = np.argmin(np.abs(self.imp1.t_tilted + 30 - self.imp1.timestamps))
        baseline_ind2 = np.argmin(np.abs(self.imp1.t_tilted + 90 - self.imp1.timestamps))
        # eot_ind = np.argmin(np.abs(self.imp1.t_end - self.imp1.timestamps))
        baseline1 = np.mean(self.substracted_1[baseline_ind1:baseline_ind2])
        baseline2 = np.mean(self.substracted_2[baseline_ind1:baseline_ind2])
        avg_window = 20
        # x = np.arange(0, np.floor((np.floor(self.imp1.timestamps[eot_ind])-np.floor(self.imp1.timestamps[baseline_ind2]))), avg_window)
        y1 = []
        y2 = []
        current_ind = baseline_ind2
        next_ind = []
        while current_ind <= np.argmin(np.abs(self.imp1.t_end - avg_window - self.imp1.timestamps)):
            next_ind = np.argmin(np.abs(self.imp1.timestamps - (self.imp1.timestamps[current_ind] + avg_window)))
            y1.append(np.mean(self.substracted_1[current_ind:next_ind]))
            y2.append(np.mean(self.substracted_2[current_ind:next_ind]))
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
        axs[0].set_title("Thoracic Impedance change between tilt+90s and EoT (Normalized)")
        axs[0].set_xlabel("Time after tilt (s)")
        axs[0].set_ylabel("Percentage impedance change (%)")
        axs[0].set_xlim(min(x), max(x))
        axs[1].bar(x, y2, width=avg_window)
        axs[1].set_title("Splanchnic Impedance change between tilt+90s and EoT (Normalized)")
        axs[1].set_xlabel("Time after tilt (s)")
        axs[1].set_ylabel("Percentage impedance change (%)")
        axs[1].set_xlim(min(x), max(x))
        for i, v in enumerate(y1):
            if v >= 0:
                axs[0].text(i * avg_window + 90, v + 0.005, str(round(v, 2)), ha='center', fontsize=7)
            if v < 0:
                axs[0].text(i * avg_window + 90, v - 0.005, str(round(v, 2)), ha='center', fontsize=7)
        for i, v in enumerate(y2):
            if v >= 0:
                axs[1].text(i * avg_window + 90, v + 0.005, str(round(v, 2)), ha='center', fontsize=7)
            if v < 0:
                axs[1].text(i * avg_window + 90, v - 0.005, str(round(v, 2)), ha='center', fontsize=7)
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
        self.Average_window_length = 60

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
        sysmin6 = np.min(self.bpecg.sysfi[sysmin6_ind:sysmax6_ind + 1])
        sysmax6 = np.max(self.bpecg.sysfi[sysmin6_ind:sysmax6_ind + 1])
        diaavg6 = np.mean(self.bpecg.diafi[diamin6_ind:diamax6_ind + 1])
        diamin6 = np.min(self.bpecg.diafi[diamin6_ind:diamax6_ind + 1])
        diamax6 = np.max(self.bpecg.diafi[diamin6_ind:diamax6_ind + 1])
        #pulsemin6 = np.min()
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
        for plot in [self.plot3, self.plot2, self.plot4, self.plot5, self.plot6]:
            vline_item = pg.InfiniteLine(angle=90, movable=True)
            plot.addItem(vline_item)
            self.vline_items.append(vline_item)
            vline_item.sigPositionChanged.connect(self.update_vlines)

    def update_vlines(self):
        self.xPos = self.vline_items[0].value()
        print(f'xPos is {self.xPos}')
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
        imp1I_ind = np.argmin(np.abs(self.xPos - self.imp1.timestamps))
        imp2I_ind = np.argmin(np.abs(self.xPos - self.imp2.timestamps))
        mapI_ind = np.argmin(np.abs(self.xPos - self.bpecg.maptime))
        hrI_ind = np.argmin(np.abs(self.xPos - self.bpecg.hrtime))
        apI_ind = np.argmin(np.abs(self.xPos - self.bpecg.aptime))
        imp1diff = self.imp1_m[imp1I_ind] / imp1avgR * 100 - 100
        imp2diff = self.imp2_m[imp2I_ind] / imp2avgR * 100 - 100
        mapdiff = self.bpecg.mapfi[mapI_ind] / mapavgR * 100 - 100
        hrdiff = self.bpecg.hr[hrI_ind] / hravgR * 100 - 100
        apdiff = self.bpecg.ap[apI_ind] / apavgR * 100 - 100
        self.relative_change_label.setText(
            f'The baseline data is between {round(self.xminR, 2)}s and {round(self.xmaxR, 2)}s'
            f'\nThe current data point for relative change calculation is {round(self.xPos, 2)}s'
            f'\nThoracic Impedance change is {round(imp1diff, 2)}%'
            f'\nSplanchnic Impedance change is {round(imp2diff, 2)}%'
            f'\nHeart Rate change is {round(hrdiff, 2)}%'
            f'\nMAP change is {round(mapdiff, 2)}%')
        for vline_item in self.vline_items:
            vline_item.setValue(self.vline_items[0].value())

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
        self.imp1_m = AvgAbsImp1NoOL
        self.imp2_m = AvgAbsImp2NoOL

    def ref_freq(self):
        freqwanted = 100000
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
        self.imp1_ref = AvgAbsImp1NoOL
        self.imp2_ref = AvgAbsImp2NoOL
    def update_plot2(self):
        # Get the selected region
        xmin, xmax = self.selection_region.getRegion()

        # Update the second plot with the selected region
        # self.plot2.clear()
        x = self.bpecg.maptime
        y = self.bpecg.mapfi
        self.plot2.plot(x, y)
        self.plot2.setTitle('MAP')
        # Set the range of the second plot to the selected region
        for plot in [self.plot2, self.plot3, self.plot4, self.plot5, self.plot6]:
            plot.setXRange(xmin, xmax)
            plot.setLimits(xMin=xmin, xMax=xmax)
        print(xmin)
        print(xmax)


if __name__ == '__main__':
    app = QtWidgets.QApplication()
    window = Startup()
    window.show()
    app.exec()
