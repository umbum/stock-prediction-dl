#-*- coding: cp949 -*-
#-*- coding: utf-8 -*- 

# ����� �����͸� �ҷ��� �н��� �����ϰ� �ϱ� ���� ����ȭ ��Ų��.
# ����ȭ�� �����͸� �̿��Ͽ� ���� ���� �н���Ų��.
# �� epoch ���� �н� �� ���Ͽ� ���� �����Ѵ�.
# ������ �����ϴ� ȸ�͸�

import numpy as np
from TI_GRU_k_updown import get_model
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from keras.optimizers import *
from keras.models import Model
from sklearn.metrics import roc_curve
from scipy.optimize import brentq
from scipy.interpolate import interp1d
import os
import yaml
import matplotlib.pyplot as plt
import keras.backend.tensorflow_backend as KK



# gpu����
def get_session(gpu_fraction=0.1):
	'''Assume that you have 8GB of GPU memory and want to allocate ~1.6GB'''

	num_threads = os.environ.get('OMP_NUM_THREADS')
	gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=gpu_fraction)

	if num_threads:
		return tf.Session(config=tf.ConfigProto(
			gpu_options=gpu_options, allow_soft_placement=True, intra_op_parallelism_threads=num_threads))
	else:
		return tf.Session(config=tf.ConfigProto(gpu_options=gpu_options,allow_soft_placement=True))

KK.set_session(get_session())
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
	y_temp = np.load(stock_name+'_y_label.npy', allow_pickle=True)
	x_temp = normalize_data(x_temp[33:-1],11)			# 34��° ������ ���� �����Ͱ� ����, �����������ʹ� ���� �� �� ���⿡ ����
	close = normalize_data(data_temp[34+time_step:, 1],1)			# time_stpe���� 35��° ���� ���� ����

	x_label = []

	for index in range(len(x_temp) - time_step): 
		x_label.append(x_temp[index: index + time_step])

	return (np.array(x_label), np.array(y_temp[134:]),np.array(close))

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

def calculate_eer(model, path, data_x, data_y,x_dev_label,parser):
	y_score = []
	model.load_weights(path)
	t = Model(inputs=model.get_layer('input_1').input, outputs=model.get_layer('code').output)
	results = model.predict(data_x)
	
	t_vector = t.predict(x_dev_label,batch_size=parser['batch_size'], verbose = 1, steps = None)
	

	for i in range(len(results)):
		if results[i][1]>0.5:
			y_score.append(1)
		else:
			y_score.append(0)
	
	fpr, tpr, thresholds = roc_curve(data_y, y_score, pos_label=1)
	eer = brentq(lambda x: 1. - x - interp1d(fpr, tpr)(x), 0., 1.)

	return (1-eer)*100

if __name__ == '__main__':
	#yaml���� �ε�
	_abspath = os.path.abspath(__file__)
	dir_yaml = 'C:\\Users\\thwjd\\sourc\\Capston\\04_model_k_updown_train.yaml'
	with open(dir_yaml, 'r', encoding='UTF8') as f_yaml:
		parser = yaml.load(f_yaml)
	
	x_label, y_label, normal_close = load_data('./kospi',100)	
	
	leng = len(x_label)			
	
	# development_set�� 0.9 validation_set�� 0.1�� �����.
	x_dev_label = x_label[:int(leng*0.9),:,:]	# 19961226 ~ 20160621
	x_val_label = x_label[int(leng*0.9):,:,:]
	y_val_label = y_label[int(leng*0.9):]


	model, m_name = get_model(argDic = parser['model'])

	eer = calculate_eer(model,'E:/source/stock_predict/networks/kospi_updown_predict_model001/1223-0.0360-0.4426.h5',
			   x_val_label,y_val_label,x_dev_label,parser)

	print("��� ������ = %.3f%%"%eer)