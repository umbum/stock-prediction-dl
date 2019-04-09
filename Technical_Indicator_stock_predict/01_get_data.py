#!/usr/bin/python
#-*- coding: cp949 -*-
#-*- coding: utf-8 -*- 

#	���� CybosPlus�� �����Ѵ�.
#	Ư���� �ְ��� ����	1996/12/26�Ϻ��� ������� �ְ� ������ �޾ƿ´�.
#	�ְ������� ����� ��ǥ�� ����ϰ� ������ �����Ѵ�.
#
import sys
from PyQt5.QtWidgets import *
import win32com.client
import pandas as pd
import os
import talib
import numpy as np

g_objCodeMgr = win32com.client.Dispatch('CpUtil.CpCodeMgr')
g_objCpStatus = win32com.client.Dispatch('CpUtil.CpCybos')
 
 
class CpStockChart:
	def __init__(self):
		self.objStockChart = win32com.client.Dispatch("CpSysDib.StockChart")
 
    # ��Ʈ ��û - �Ⱓ ��������
	def RequestFromTo(self, code, fromDate, toDate, caller):
		print(code, fromDate, toDate)
		# ���� ���� üũ
		bConnect = g_objCpStatus.IsConnect
		if (bConnect == 0):
			print("PLUS�� ���������� ������� ����. ")
			return False
 
		self.objStockChart.SetInputValue(0, code)  # �����ڵ�
		self.objStockChart.SetInputValue(1, ord('1'))  # �Ⱓ���� �ޱ�
		self.objStockChart.SetInputValue(2, toDate)  # To ��¥
		self.objStockChart.SetInputValue(3, fromDate)  # From ��¥
		self.objStockChart.SetInputValue(5, [0, 2, 3, 4, 5, 8])  # ��¥,�ð�,��,����,����,�ŷ���
		self.objStockChart.SetInputValue(6, ord('D'))  # '��Ʈ �ֱ� - �ϰ� ��Ʈ ��û
		self.objStockChart.SetInputValue(9, ord('1'))  # �����ְ� ���
		self.objStockChart.BlockRequest()
 
		rqStatus = self.objStockChart.GetDibStatus()
		rqRet = self.objStockChart.GetDibMsg1()
		print("��Ż���", rqStatus, rqRet)
		if rqStatus != 0:
			exit()
 
		len = self.objStockChart.GetHeaderValue(3)
 
		for i in range(len):
			caller.dates.append(self.objStockChart.GetDataValue(0,len - i - 1))
			caller.opens.append(self.objStockChart.GetDataValue(1, len - i - 1))
			caller.highs.append(self.objStockChart.GetDataValue(2, len - i - 1))
			caller.lows.append(self.objStockChart.GetDataValue(3, len - i - 1))
			caller.closes.append(self.objStockChart.GetDataValue(4, len - i - 1))
			caller.vols.append(self.objStockChart.GetDataValue(5, len - i - 1))
 
		print(len)
 
class MyWindow(QMainWindow):
	def __init__(self):
		super().__init__()
 
        # �⺻ ������
		self.dates = []
		self.opens = []
		self.highs = []
		self.lows = []
		self.closes = []
		self.vols = []
		self.macd = []
		self.ema = []
		self.momentum = []
		self.slowk= []
		self.slowd= []
		self.objChart = CpStockChart()
		self.willr = []
		self.upband = []
		self.lowband =[] 
		self.rsi = []
		self.roc =[]
		self.obv =[]
		self.y_label=[]
		# ������ ��ư ��ġ
		self.setWindowTitle("PLUS API TEST")
		nH = 20
 
		self.codeEdit = QLineEdit("", self)
		self.codeEdit.move(20, nH)
		self.codeEdit.textChanged.connect(self.codeEditChanged)
		self.codeEdit.setText('00660')
		self.label = QLabel('�����ڵ�', self)
		self.label.move(140, nH)
		nH += 50
 
		btchart1= QPushButton("�Ⱓ(�ϰ�) ��û", self)
		btchart1.move(20, nH)
		btchart1.clicked.connect(self.btchart1_clicked)
		nH += 50

		btchart1= QPushButton("��ǥ ���", self)
		btchart1.move(20, nH)
		btchart1.clicked.connect(self.btchart2_clicked)
		nH += 50

		btchart7 = QPushButton("������ ����", self)
		btchart7.move(20, nH)
		btchart7.clicked.connect(self.btchart7_clicked)
		nH += 50
 
		btnExit = QPushButton("����", self)
		btnExit.move(20, nH)
		btnExit.clicked.connect(self.btnExit_clicked)
		nH += 50
 
		self.setGeometry(300, 300, 300, nH)
		self.setCode('A000660')
 
	# �Ⱓ(�ϰ�) ���� �ޱ�
	def btchart1_clicked(self):
		if self.objChart.RequestFromTo(self.code, 19961226, 20051007, self) == False:
			exit()
		if self.objChart.RequestFromTo(self.code, 20051010, 20190329, self) == False:
			exit()
		self.y_label.append(None)
		for i in range(len(self.closes)-1):
			self.y_label.append((self.closes[i+1]-self.closes[i])/self.closes[i])

	def btchart2_clicked(self):
		close = np.array(self.closes,dtype=float)
		high = np.array(self.highs,dtype=float)
		low = np.array(self.lows,dtype=float)
		vol = np.array(self.vols,dtype = float)
		self.macd, macdsignal,macdhist = talib.MACD(close)
		self.ema = talib.EMA(close)
		self.momentum = talib.MOM(close)
		self.slowk, self.slowd = talib.STOCH(high,low,close)
		self.roc = talib.ROC(close)
		self.willr = talib.WILLR(high,low,close)
		self.ad = talib.AD(high,low,close,vol)
		self.rsi = talib.RSI(close)
		self.obv = talib.OBV(close,vol)
		self.upband, middle, self.lowband = talib.BBANDS(close)
		print('��ǥ��� �Ϸ�')

	def btchart7_clicked(self):
		charfile = 'chart.xlsx'
        
		chartData = {'����' : self.dates,
					'�ð�' : self.opens,
					'��' : self.highs,
					'����' : self.lows,
					'����' : self.closes,
					'�ŷ���' : self.vols,
					'MACD' : self.macd,
					'EMA' : self.ema,
					'Momentum' : self.momentum,
					'slowK' : self.slowk,
					'slowD' : self.slowd,
					'ROC' : self.roc,
					'william_R' : self.willr,
					'A/D': self.ad,
					'RSI': self.rsi,
					'OBV' : self.obv,
					'upperband': self.upband,
					'lowerband': self.lowband,
					'�������������' : self.y_label,
					}
		df =pd.DataFrame(chartData, columns=['����','�ð�','��','����','����','�ŷ���','MACD','EMA','Momentum','slowK','slowD','ROC','william_R','A/D','RSI','OBV','upperband','lowerband','�������������'])
      
 
		df = df.set_index('����')
 
		# create a Pandas Excel writer using XlsxWriter as the engine.
		writer = pd.ExcelWriter(charfile, engine='xlsxwriter')
		# Convert the dataframe to an XlsxWriter Excel object.
		df.to_excel(writer, sheet_name='Sheet1')
		# Close the Pandas Excel writer and output the Excel file.
		writer.save()
		os.startfile(charfile)
		return
 
	def codeEditChanged(self):
		code = self.codeEdit.text()
		self.setCode(code)
 
	def setCode(self, code):
		if len(code) < 6:
			return
 
		print(code)
		if not (code[0] == "A"):
			code = "A" + code
 
		name = g_objCodeMgr.CodeToName(code)
		if len(name) == 0:
			print("�����ڵ� Ȯ��")
			return
 
		self.label.setText(name)
		self.code = code
 
 
	def btnExit_clicked(self):
		exit()
 
 
 
if __name__ == "__main__":
	app = QApplication(sys.argv)
	myWindow = MyWindow()
	myWindow.show()
	app.exec_()