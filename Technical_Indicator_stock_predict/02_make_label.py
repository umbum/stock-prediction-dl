#-*- coding: cp949 -*-
#-*- coding: utf-8 -*- 

#	data ������ ����� �������� �ҷ��´�.
#	����, �ð�, ��, ����, ����, �ŷ����� �ְ��̸�_data�� ����
#	MACD, EMA, Momentum, SlowK, SlowD, ROC, William_R, A/D, RSI, OBV, upperband, lowerband�� ����� ��ǥ�μ� �н��� ���� �ְ��̸�_X_label�� ����
#	������� �������� �ְ��̸�_y_label�� ����

from openpyxl import load_workbook
import numpy as np
import os

if __name__ == '__main__': 
	
	for root, dirs, files in os.walk('./data'):
		for file in files:
			filename = file[:-5]
			
			filedata = load_workbook('./data/'+file)

			sheet1 = filedata['Sheet1']

			sheet2 = filedata.active

			print(sheet1['D4'].value)
			print(sheet2['D4'].value)
			datas = []
			x_labels = []
			y_labels = []

			for i in sheet1.rows:
				data=[]

				for d in i:
					data.append(d.value)

				datas.append(data[:6])
				x_labels.append(data[6:-1])
				y_labels.append(data[-1])

			np.save('./data_label/'+filename+'_data.npy',datas)
			np.save('./data_label/'+filename+'_x_label.npy',x_labels)
			np.save('./data_label/'+filename+'_y_label.npy',y_labels)
			
