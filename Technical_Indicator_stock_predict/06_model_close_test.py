#-*- coding: cp949 -*-
#-*- coding: utf-8 -*- 

# ����� �����͸� �ҷ��� �н��� �����ϰ� �ϱ� ���� ����ȭ ��Ų��.
# ����ȭ�� �����͸� �̿��Ͽ� ���� ���� �н���Ų��.
# �� epoch ���� �н� �� ���Ͽ� ���� �����Ѵ�.
# ������ �����ϴ� ȸ�͸�

import numpy as np
from TI_GRU_close import get_model
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from keras.optimizers import *
from keras.models import Model
import os
import yaml
import matplotlib.pyplot as plt

def normalize_data(data, length):		# ������ ������ 0,1 ���̷� ��ȯ��Ų��. 
	min_max_scaler = MinMaxScaler()

	if length == 1:						#�����Ͱ� 1���� �� ���
		n_data = min_max_scaler.fit_transform(data.reshape(-1,1))
		return n_data

	#�����Ͱ� N���� �� ���
	n_data =  min_max_scaler.fit_transform(data[:,0].reshape(-1,1))

	for i in range(length-1):
		i = i+1
		tmp = min_max_scaler.fit_transform(data[:,i].reshape(-1,1))
		n_data = np.concatenate((n_data,tmp),axis = 1)

	return n_data

#�ְ� �����͸� �ҷ����� ����ȭ���� ��Ų��.
def load_data(stock_name, time_step):		
	data_temp = np.load(stock_name+'_data.npy', allow_pickle=True)
	x_temp = np.load(stock_name+'_x_label.npy', allow_pickle=True)
	
	x_temp = normalize_data(x_temp[34:-1],12)			# 34��° ������ ���� �����Ͱ� ����, �����������ʹ� ���� �� �� ���⿡ ����
	close = normalize_data(data_temp[35+time_step:, 4],1)			# time_stpe���� 35��° ���� ���� ����
	
	x_label = []

	for index in range(len(x_temp) - time_step): # 100���� Ÿ�ӽ����� ���� x_label�� ����
		x_label.append(x_temp[index: index + time_step])

	return (np.array(x_label), np.array(close))

def save_graph(y1,y2, epoch,val_mae, save_dir = None ):
	x = range(len(y1))
	plt.plot(x, y1, label = 'target')
	plt.plot(x, y2, label = 'predict')

	plt.xlabel('day')
	plt.ylabel('close')

	plt.title('%d_prediction val = %.5f'%(epoch,val_mae))
	plt.legend()

	if save_dir != None:
		plt.savefig(save_dir+'%d_prediction.png'%epoch, format='png')
		plt.clf() 
		return 0
	plt.show()

def predict_model(model, path,x_val_label, x_label, under, close_min ):
	model.load_weights(path)
	temp = path.split('/')[-1]
	epoch = temp.split('-')[0]
	predict = temp.split('-')[-1].split('.')[0]
	result = model.predict(x_val_label, batch_size=parser['batch_size'], verbose=1, steps=None)
	close_predict = (result*under)+close_min
	save_graph(x_label, close_predict, int(epoch), int(predict), )



if __name__ == '__main__':
	#yaml���� �ε�
	_abspath = os.path.abspath(__file__)
	dir_yaml = 'C:\\Users\\thwjd\\sourc\\Capston\\03_model_close_train.yaml'
	with open(dir_yaml, 'r', encoding='UTF8') as f_yaml:
		parser = yaml.load(f_yaml)
	
	data_temp = np.load('./data_label/SK���̴н�_data.npy')
	non_norm_close = []
	
	for i in data_temp[135:,4]:		# 34+100+1 -> 34������ ����� ��ǥ�� ��� ����, timestep 100, �Ϸ�� ���� 1
		non_norm_close.append(float (i))
	
	non_norm_close = np.array(non_norm_close)
	
	non_norm_close = non_norm_close[:,np.newaxis]	# �����͸� 1���� �ø���.
	
	close_min = min(non_norm_close)
	close_max = max(non_norm_close)
	
	under = close_max - close_min		# ���� ����ȭ�� ����� ������ �ٽ� ����ϱ� ����
	
	x_label, normal_close = load_data('./data_label/SK���̴н�',100)	
	
	leng = len(x_label)			
	
	# development_set�� 0.9 validation_set�� 0.1�� �����.
	
	x_val_label = x_label[int(leng*0.9):,:,:]


	model, m_name = get_model(argDic = parser['model'])

	predict_model(model,'C:/Users/thwjd/source/stock_predict/networks/sk_predict_model010/1012-0.0103-1860.3714.h5',
			   x_val_label,non_norm_close[int(leng*0.9):],under,close_min)