from cmath import nan
import os
import logging
import datetime
import csv
import fnmatch

import pandas as pd
import scipy
from sqlite3 import Time
from wsgiref.simple_server import software_version
from scipy.signal import find_peaks
import matplotlib.pyplot as plt
import numpy as np

from pathlib import Path


class Nova:
    def __init__(self, data_folder):
        self.path = Path(data_folder)
        ParentPath =data_folder
        os.chdir(data_folder)
        pattern='*Raw'
        #print('Pattern :',pattern)
        files=os.listdir()
        for name in files:
            #print ('Filename: %s %s' % (name, fnmatch.fnmatch(name, pattern)))
            if fnmatch.fnmatch(name,pattern)==True:
                foldername=name
        print("The folder name is:",foldername)
        os.chdir(ParentPath + '/' + foldername)
        files=os.listdir()

        # Code for beat-by-beat bp reading
        try:
            for name in files:
                if fnmatch.fnmatch(name,'*fiAPLvl.csv')==True:
                    apname=name
            print("The file is", apname)
            apfile=(ParentPath+'/'+foldername+'/'+apname)
            with open(apfile,"r") as csv_f:
                   bpsoftware_version=csv_f.readline().strip("\n")
                   bpSN=csv_f.readline().strip("\n")
                   bphardware_config=csv_f.readline().strip("\n")
                   csv_f.readline().strip("\n")
                   bpinfo1=csv_f.readline().strip("\n")
                   bpinfo2=csv_f.readline().strip("\n")
                   csv_f.readline().strip("\n")

                   time=[]
                   fi=[]
                   marker=[]
                   region=[]

                   reader=csv.DictReader(csv_f,delimiter=";")
                   for row in reader:
                       time.append(float(row['Time(sec)']))
                       fi.append(float(row['fiAPLvl(mmHg)']))
                       marker.append(row['Marker'])
                       region.append(row['Region'])
                       # print(f'The current row is {row}')
                   self.aptime=time
                   self.ap=fi
                   self.apmarker=marker
                   self.apregion=region
        except:
            for name in files:
                if fnmatch.fnmatch(name, '*fiAP.csv') == True:
                    apname = name
            print("The file is", apname)
            apfile = (ParentPath + '/' + foldername + '/' + apname)
            with open(apfile, "r") as csv_f:
                bpsoftware_version = csv_f.readline().strip("\n")
                bpSN = csv_f.readline().strip("\n")
                bphardware_config = csv_f.readline().strip("\n")
                csv_f.readline().strip("\n")
                bpinfo1 = csv_f.readline().strip("\n")
                bpinfo2 = csv_f.readline().strip("\n")
                csv_f.readline().strip("\n")

                time = []
                fi = []
                marker = []
                region = []

                reader = csv.DictReader(csv_f, delimiter=";")
                for row in reader:
                    time.append(float(row['Time(sec)']))
                    try:
                        fi.append(float(row['fiAP(mmHg)']))
                    except:
                        fi.append(np.nan)
                    marker.append(row['Marker'])
                    region.append(row['Region'])
                    print(f'The current row is {row}')
                self.aptime = time
                self.ap = fi
                self.apmarker = marker
                self.apregion = region


        ap_df = pd.DataFrame({
            'timestamp': self.aptime,
            'value': self.ap
        })
        ap_df.to_excel(excel_writer=ParentPath+'/impfile/ap.xlsx')


        # Code for HR reading

        for name in files:
            if fnmatch.fnmatch(name,'*HR AP.csv')==True:
                hrname=name
        print("The file is", hrname)
        hrfile=(ParentPath+'/'+foldername+'/'+hrname)
        with open(hrfile,"r") as csv_f:
               hrsoftware_version=csv_f.readline().strip("\n")
               hrSN=csv_f.readline().strip("\n")
               hrhardware_config=csv_f.readline().strip("\n")
               csv_f.readline().strip("\n")
               hrinfo1=csv_f.readline().strip("\n")
               hrinfo2=csv_f.readline().strip("\n")
               csv_f.readline().strip("\n")

               time=[]
               hr=[]
               marker=[]
               region=[]
               hrv=[]
               reader=csv.DictReader(csv_f,delimiter=";")
               for row in reader:
                   time.append(float(row['Time(sec)']))
                   hr.append(float(row['HR AP(bpm)']))
                   marker.append(row['Marker'])
                   region.append(row['Region'])
                   hrv.append(60000/float(row['HR AP(bpm)']))
               self.hrtime=time
               self.hr=hr
               self.hrmarker=marker
               self.hrregion=region
               self.hrv=hrv
        hr_df = pd.DataFrame({
            'timestamp': self.hrtime,
            'value': self.hr
        })
        hr_df.to_excel(excel_writer=ParentPath + '/impfile/hr.xlsx')


        # Code for bp reading

        for name in files:
            if fnmatch.fnmatch(name,'*fiSYS*')==True:
                sysname=name
        print("The sysname is", sysname)
        for name in files:
            if fnmatch.fnmatch(name,'*fiDIA*')==True:
                dianame=name
        for name in files:
            if fnmatch.fnmatch(name,'*fiMAP.csv')==True:
                mapname=name
        print("The dianame is", dianame)
        bpnamesdir=[]
        bpnamesdir.append(ParentPath+'/'+foldername+'/'+dianame)
        bpnamesdir.append(ParentPath+'/'+foldername+'/'+sysname)
        bpnamesdir.append(ParentPath+'/'+foldername+'/'+mapname)
        print("bpmames is ",bpnamesdir,"\n")
        counter=0
        for bpfile in bpnamesdir:
            counter=counter+1
            print("current file is: ", bpfile)
            if counter==1:
                bpname="fiDIA"
            if counter==2:
                bpname="fiSYS"
            if counter==3:
                bpname="fiMAP"
            with open(bpfile,"r") as csv_f:
                bpsoftware_version=csv_f.readline().strip("\n")
                bpSN=csv_f.readline().strip("\n")
                bphardware_config=csv_f.readline().strip("\n")
                csv_f.readline().strip("\n")
                bpinfo1=csv_f.readline().strip("\n")
                bpinfo2=csv_f.readline().strip("\n")
                csv_f.readline().strip("\n")

                time=[]
                fi=[]
                marker=[]
                region=[]
            
                reader=csv.DictReader(csv_f,delimiter=";")
                sysmissing=[]
                for row in reader:
                    time.append(float(row['Time(sec)']))
                    try:
                        fi.append(float(row[bpname+'(mmHg)']))
                    except:
                        fi.append(np.nan)
                        sysmissing=1
                    marker.append(row['Marker'])
                    region.append(row['Region'])
                if counter==1:
                    self.diatime=time
                    self.diafi=fi
                    self.diamarker=marker
                    self.diaregion=region
                
                if counter==2: #and sysmissing!=1:
                    self.systime=time
                    self.sysfi=fi
                    self.sysmarker=marker
                    self.sysregion=region
                if counter==3:
                    self.maptime=time
                    self.mapfi=fi
                    self.mapmarker=marker
                    self.mapregion=region
                    # if sysmissing==1:
                    #     print("Systolic BP misssing, using MAP instead")
                    #     self.systime=self.maptime
                    #     self.sysfi=self.mapfi
                    #     self.sysmarker=self.mapmarker
                    #     self.sysregion=self.mapregion
        sys_df = pd.DataFrame({
            'timestamp': self.systime,
            'value': self.sysfi
        })
        sys_df.to_excel(excel_writer=ParentPath + '/impfile/sys.xlsx')
        dia_df = pd.DataFrame({
            'timestamp': self.diatime,
            'value': self.diafi
        })
        dia_df.to_excel(excel_writer=ParentPath + '/impfile/dia.xlsx')
        map_df = pd.DataFrame({
            'timestamp': self.maptime,
            'value': self.mapfi
        })
        map_df.to_excel(excel_writer=ParentPath + '/impfile/map.xlsx')
        
        

        
        # BP reading finished, start ECG reading

        for name in files:
            if fnmatch.fnmatch(name,'*ECG I.csv')==True:
                ecg1name=name
            if fnmatch.fnmatch(name,'*ECG II.csv')==True:
                ecg2name=name
            if fnmatch.fnmatch(name,'*ECG III.csv')==True:
                ecg3name=name
        #print("The ecg1 is", ecg1name)
        #print("The ecg2 is", ecg2name)
        #print("The ecg3 is", ecg3name)
        ecgnamedir=[]
        ecgnamedir.append(ParentPath+'/'+foldername+'/'+ecg1name)
        ecgnamedir.append(ParentPath+'/'+foldername+'/'+ecg2name)
        ecgnamedir.append(ParentPath+'/'+foldername+'/'+ecg3name)
        #print("ecgnames are ",ecgnamedir)
        counter=0
        for ecgfile in ecgnamedir:
            counter=counter+1
            print("current file is: ", ecgfile)
            if counter==1:
                ecgname="ECG I"
            if counter==2:
                ecgname="ECG II"
            if counter==3:
                ecgname="ECG III"
            with open(ecgfile,"r") as csv_f:
                ecgsoftware_version=csv_f.readline().strip("\n")
                ecgSN=csv_f.readline().strip("\n")
                ecghardware_config=csv_f.readline().strip("\n")
                csv_f.readline().strip("\n")
                ecginfo1=csv_f.readline().strip("\n")
                ecginfo2=csv_f.readline().strip("\n")
                csv_f.readline().strip("\n")

                time=[]
                ecg=[]
                marker=[]
                region=[]

                reader=csv.DictReader(csv_f,delimiter=";")
                for row in reader:
                    time.append(float(row['Time(sec)']))
                    if row[ecgname+'(mV)']=="":
                        ecg.append(0)
                    else:
                        ecg.append(float(row[ecgname+'(mV)']))
                    marker.append(row['Marker'])
                    region.append(row['Region'])
                if counter==1:
                    time1=time
                    ecg1=ecg
                    marker1=marker
                    region1=region
                if counter==2:
                    time2=time
                    ecg2=ecg
                    marker2=marker
                    region2=region
                if counter==3:
                    time3=time
                    ecg3=ecg
                    marker3=marker
                    region3=region
        if time1==time2 and time2==time3:
            self.ecg=[x+y+z for x,y,z in zip(ecg1,ecg2,ecg3)]
            self.ecgtime=time1
        else:
            raise Exception("Time in ECG I II III don't match, check your data")

        self.pp = np.subtract(self.sysfi, self.diafi)



        # peaks, _ = find_peaks(self.ap)
        # self.ap_peak = []
        # self.ap_trough = []
        # for idx in peaks:
        #     # print(f"Peak found at index {idx}, value {self.ap[idx]}")
        #     self.ap_peak.append(self.ap[idx])
        # negap = [-x for x in self.ap]
        # troughs, _ = find_peaks(negap)
        # for idx in troughs:
        #     # print(f"Trough found at index {idx}, value {self.ap[idx]}")
        #     self.ap_trough.append(self.ap[idx])
        # print(f'length of peaks is {len(peaks)}, length of ap_peak is {len(self.ap_peak)}')
        # print(f'the first peak is at {self.aptime[peaks[1]]}, the last peak is at {self.aptime[peaks[-1]]}')
        # self.ap_peak_f = scipy.interpolate.interp1d(peaks,self.ap_peak)
        # self.ap_trough_f = scipy.interpolate.interp1d(troughs,self.ap_trough)
        # self.ap_peak_env = self.ap_peak_f(self.aptime)
        # self.ap_trough_env = self.ap_trough_f(self.aptime)
        # self.pulse_pressure = self.ap_peak_env - self.ap_trough_env
        # plt.plot(self.aptime,self.pulse_pressure)
        # plt.plot(self.aptime,self.ap)
        # plt.show()
        #if 'sys'


                                
        



        #glob.glob('* Raw')
        #print(bpecgpath)
        #self.path = Path(data_folder / bpecgpath)
        #print(os.getcwd())
        #logging.info(f'reading {self.path}')
        #files = sorted(os.listdir(self.path))
        #files = [os.path.join(self.path, x) for x in files if x.endswith(".spec")]

        #timestamps = []
        #all_real_ohm = []
        #all_imag_ohm = []
        #filenum=0
        #for file in files:
        #    logging.info(file)
        #    with open(file, "r") as csv_f:
        #        unknown = csv_f.readline().strip("\n")
        #        fn = csv_f.readline().strip("\n")
        #        offset = csv_f.readline().strip("\n")
        #        channels = csv_f.readline().strip("\n")
        #        if channels == "Overvoltage detected":
        #            channels = csv_f.readline().strip("\n")
        #            logging.warning("Overvoltage detected")
        #            #continue
        #        timestamp = csv_f.readline().strip("\n")
        #        timestamp = datetime.datetime.strptime(timestamp, '%d-%b-%Y %I:%M:%S:%f %p')
        #        timestamps.append(timestamp)

        #        freq = []
        #        real_ohm = []
        #        imag_ohm = []

        #        reader = csv.DictReader(csv_f)
        #        for row in reader:
        #            freq.append(float(row['frequency[Hz]']))
        #            real_ohm.append(float(row['Re[Ohm]']))
        #            imag_ohm.append(float(row['Im[Ohm]']))
                
        #    all_real_ohm.append(real_ohm)
        #    all_imag_ohm.append(imag_ohm)
        #    filenum=filenum+1

        #self.freq = np.array(freq)
        #first_timestamp = min(timestamps)
        #time = [(x-first_timestamp).total_seconds() for x in timestamps]

        #sort_idx = sorted(range(len(time)), key=lambda k: time[k])

        #self.timestamps = np.array(time)[sort_idx]
        #self.real_ohm_np = np.array(all_real_ohm)[sort_idx]
        #self.imag_ohm_np = np.array(all_imag_ohm)[sort_idx]
        #self.abs_ohm_np = np.sqrt(self.real_ohm_np ** 2 + self.imag_ohm_np ** 2)
        #self.filenum=filenum