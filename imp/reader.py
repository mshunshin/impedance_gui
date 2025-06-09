import os
import logging
import datetime
import csv
import pickle
from sqlite3 import Timestamp

import numpy as np
import scipy.io as sio

from pathlib import Path


class Sciospec:
    def __init__(self, data_folder, num):

        self.path = Path(data_folder)
        ParentPath = self.path.parents[1]
        timepoints = ParentPath / 'timepoints.txt'
        impfilepath = ParentPath / 'impfile'
        testfile = impfilepath / 'freq2.txt'

        if num > 2:
            testfile = Path(impfilepath) / 'freq3.txt'

        isFile = os.path.isfile(testfile)

        print(f"The path is {ParentPath}")

        if not isFile:
            logging.info(f'reading {self.path}')
            files = sorted(os.listdir(self.path))
            files = [os.path.join(self.path, x) for x in files if x.endswith(".spec")]

            timestamps = []
            all_real_ohm = []
            all_imag_ohm = []
            filenum = 0

            for file in files:
                logging.info(file)
                with open(file, "r") as csv_f:
                    unknown = csv_f.readline().strip("\n")
                    fn = csv_f.readline().strip("\n")
                    offset = csv_f.readline().strip("\n")
                    channels = csv_f.readline().strip("\n")
                    if channels == "Overvoltage detected":
                        channels = csv_f.readline().strip("\n")
                        logging.warning("Overvoltage detected")
                        # continue
                    timestamp = csv_f.readline().strip("\n")
                    timestamp = datetime.datetime.strptime(timestamp, '%d-%b-%Y %I:%M:%S:%f %p')
                    timestamps.append(timestamp)

                    freq = []
                    real_ohm = []
                    imag_ohm = []

                    reader = csv.DictReader(csv_f)
                    for row in reader:
                        freq.append(float(row['frequency[Hz]']))
                        real_ohm.append(float(row['Re[Ohm]']))
                        imag_ohm.append(float(row['Im[Ohm]']))

                    # real_ohm=str(real_ohm)[1:-1]

                all_real_ohm.append(real_ohm)
                all_imag_ohm.append(imag_ohm)
                filenum = filenum + 1

            # Read time points 
            try:
                with open(impfilepath / "timepoints.txt") as time_f:
                    start = time_f.readline().strip("\n")
                    tilted = time_f.readline().strip("\n")
                    gtn = time_f.readline().strip("\n")
                    end = time_f.readline().strip("\n")
                    fneckrubl = time_f.readline().strip("\n")
                    fneckrubr = time_f.readline().strip("\n")
                    tneckrubl = time_f.readline().strip("\n")
                    tneckrubr = time_f.readline().strip("\n")
                    impoffset = time_f.readline().strip("\n")

                    t_start = datetime.datetime.strptime(start, '%H:%M:%S')
                    t_tilted = datetime.datetime.strptime(tilted, '%H:%M:%S')
                    t_end = datetime.datetime.strptime(end, '%H:%M:%S')
                    if gtn != '':
                        t_gtn = datetime.datetime.strptime(gtn, '%H:%M:%S')
                        self.t_gtn = (t_gtn - t_start).total_seconds()
                    if fneckrubl != '':
                        t_fneckrubl = datetime.datetime.strptime(fneckrubl, '%H:%M:%S')
                        t_fneckrubr = datetime.datetime.strptime(fneckrubr, '%H:%M:%S')
                        t_tneckrubl = datetime.datetime.strptime(tneckrubl, '%H:%M:%S')
                        t_tneckrubr = datetime.datetime.strptime(tneckrubr, '%H:%M:%S')
                        self.t_fneckrubl = (t_fneckrubl - t_start).total_seconds()
                        self.t_fneckrubr = (t_fneckrubr - t_start).total_seconds()
                        self.t_tneckrubl = (t_tneckrubl - t_start).total_seconds()
                        self.t_tneckrubr = (t_tneckrubr - t_start).total_seconds()
                    self.t_start = (t_start - t_start).total_seconds()
                    self.t_tilted = (t_tilted - t_start).total_seconds()
                    self.t_end = (t_end - t_start).total_seconds()
            except:
                logging.exception("Error reading timepoints.txt")

            self.freq = np.array(freq)
            first_timestamp = min(timestamps)
            time = [(x - first_timestamp).total_seconds() for x in timestamps]

            sort_idx = sorted(range(len(time)), key=lambda k: time[k])

            self.timestamps = np.array(time)[sort_idx]
            self.real_ohm_np = np.array(all_real_ohm)[sort_idx]
            self.imag_ohm_np = np.array(all_imag_ohm)[sort_idx]
            self.abs_ohm_np = np.sqrt(self.real_ohm_np ** 2 + self.imag_ohm_np ** 2)
            self.filenum = filenum

            # all_real_ohm=str(all_real_ohm)[1:-1]
            if os.path.isdir(impfilepath) == False:
                os.makedirs(os.path.join((ParentPath), 'impfile'))
            # filename= ParentPath
            with open(impfilepath / f"freq{str(num)}.txt", "w") as frequency:
                for item in self.freq:
                    frequency.write("%s\n" % item)
            with open(impfilepath / f"timestamps{str(num)}.txt", "w") as time:
                for item in self.timestamps:
                    time.write("%s\n" % item)
            with open(impfilepath / f"real_ohm{str(num)}.txt", "w") as real:
                for item in all_real_ohm:
                    real.write("%s\n" % item)
            with open(impfilepath / f"imag_ohm{str(num)}.txt", "w") as img:
                for item in all_imag_ohm:
                    img.write("%s\n" % item)
            with open(impfilepath / f"sort_idx{str(num)}.txt", "w") as idx:
                for item in sort_idx:
                    idx.write("%s\n" % item)
            # with open(ParentPath / f"abs_ohm{str(num)}.txt","w") as absimp:
            #    for item in self.abs_ohm_np:
            #        absimp.write("%s\n" % item)

            """
            testreal=[]
            with open(ParentPath / "real_ohm.txt","r") as real:
                for line in real:
                    x=line[:-1]
                    testreal.append(x)
            with open(ParentPath / "testreal.txt","w") as test:
                for item in testreal:
                    test.write("%s\n" % item)
            """

        else:
            try:
                with open(impfilepath / "timepoints.txt", "r") as time_f:
                    start = time_f.readline().strip("\n")
                    tilted = time_f.readline().strip("\n")
                    gtn = time_f.readline().strip("\n")
                    end = time_f.readline().strip("\n")
                    fneckrubl = time_f.readline().strip("\n")
                    fneckrubr = time_f.readline().strip("\n")
                    tneckrubl = time_f.readline().strip("\n")
                    tneckrubr = time_f.readline().strip("\n")

                    try:
                        impoffset = int(time_f.readline().strip("\n"))
                    except:
                        impoffset = 0

                t_start = datetime.datetime.strptime(start, '%H:%M:%S')
                t_tilted = datetime.datetime.strptime(tilted, '%H:%M:%S')
                t_end = datetime.datetime.strptime(end, '%H:%M:%S')

                if gtn != '':
                    t_gtn = datetime.datetime.strptime(gtn, '%H:%M:%S')
                    self.t_gtn = (t_gtn - t_start).total_seconds() + impoffset
                if fneckrubl != '':
                    t_fneckrubl = datetime.datetime.strptime(fneckrubl, '%H:%M:%S')
                    t_fneckrubr = datetime.datetime.strptime(fneckrubr, '%H:%M:%S')
                    t_tneckrubl = datetime.datetime.strptime(tneckrubl, '%H:%M:%S')
                    t_tneckrubr = datetime.datetime.strptime(tneckrubr, '%H:%M:%S')
                    self.t_fneckrubl = (t_fneckrubl - t_start).total_seconds() + impoffset
                    self.t_fneckrubr = (t_fneckrubr - t_start).total_seconds() + impoffset
                    self.t_tneckrubl = (t_tneckrubl - t_start).total_seconds() + impoffset
                    self.t_tneckrubr = (t_tneckrubr - t_start).total_seconds() + impoffset

                self.t_start = (t_start - t_start).total_seconds() + impoffset
                self.t_tilted = (t_tilted - t_start).total_seconds() + impoffset
                self.t_end = (t_end - t_start).total_seconds() + impoffset
            except Exception:
                logging.exception(f"failed to parse {impfilepath}")

            freq = []
            all_real_ohm = []
            all_imag_ohm = []
            abs_ohm = []
            timestamps = []
            sort_idx = []
            with open(impfilepath / f"real_ohm{num}.txt", "r") as real:
                for line in real:
                    x = line[:-1]
                    x = str(x)[1:-1]
                    x = list(map(float, x.split(',')))
                    all_real_ohm.append(np.array(x))
            with open(impfilepath / f"imag_ohm{num}.txt", "r") as img:
                for line in img:
                    x = line[:-1]
                    x = str(x)[1:-1]
                    x = list(map(float, x.split(',')))
                    all_imag_ohm.append(np.array(x))
            with open(impfilepath / f"freq{num}.txt", "r") as freqency:
                for line in freqency:
                    x = float(line[:-1])
                    freq.append(x)
            try:
                with open(impfilepath / f"timestamps{num}.txt", "r") as timer:
                    for line in timer:
                        x = float(line[:-1])
                        # x = datetime.datetime.strptime(x, '%Y-%m-%d %I:%M:%S.%f')
                        timestamps.append(x + impoffset)
            except:
                with open(impfilepath / f"timestamps{num}.txt", "r") as timer:
                    for line in timer:
                        x = float(line[:-1])
                        # x = datetime.datetime.strptime(x, '%Y-%m-%d %I:%M:%S.%f')
                        timestamps.append(x)
            with open(impfilepath / f"sort_idx{num}.txt", "r") as idx:
                for line in idx:
                    x = int(line[:-1])
                    sort_idx.append(x)
            # with open(impfilepath / f"abs_ohm{num}.txt","r") as absohm:
            #    for line in absohm:
            #        x=line[:-1]
            #        abs_ohm.append(x)

            self.freq = np.array(freq)
            # first_timestamp = min(timestamps)
            # time = [(x-first_timestamp).total_seconds() for x in timestamps]

            # sort_idx = sorted(range(len(timestamps)), key=lambda k: timestamps[k])
            self.idx = sort_idx

            self.timestamps = np.array(timestamps)
            self.real_ohm_np = np.array(all_real_ohm)[sort_idx]
            self.imag_ohm_np = np.array(all_imag_ohm)[sort_idx]
            self.abs_ohm_np = np.sqrt(self.real_ohm_np ** 2 + self.imag_ohm_np ** 2)
            self.filenum = len(self.timestamps)
