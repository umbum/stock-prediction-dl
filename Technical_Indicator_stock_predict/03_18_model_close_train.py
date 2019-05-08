#-*- coding: cp949 -*-
#-*- coding: utf-8 -*- 

# ����� �����͸� �ҷ��� �н��� �����ϰ� �ϱ� ���� ����ȭ ��Ų��.
# 21�� �ְ��� ����ȭ ���� 18���� �н���, 3���� �򰡿� ����Ѵ�.
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
import keras.backend.tensorflow_backend as KK
import matplotlib.pyplot as plt

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
	data_temp = np.load(stock_name+'_data.npy')
	x_temp = np.load(stock_name+'_x_label.npy')
	
	x_temp = normalize_data(x_temp[34:-1],12)			# 34��° ������ ���� �����Ͱ� ����, �����������ʹ� ���� �� �� ���⿡ ����
	close = normalize_data(data_temp[35+time_step:, 4],1)			# time_stpe���� 35��° ���� ���� ����
	
	x_label = []

	for index in range(len(x_temp) - time_step): # 100���� Ÿ�ӽ����� ���� x_label�� ����
		x_label.append(x_temp[index: index + time_step])

	return (np.array(x_label), np.array(close))

def save_graph(y1, y2, epoch, val_mae, save_dir = None):
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

def predict_model(model, path, x_label, under, close_min ):
	model.load_weights(path)
	result = model.predict(x_val_label, batch_size=parser['batch_size'], verbose=1, steps=None)
	close_predict = (result*under)+close_min
	save_graph(x_label, close_predict, 325, 1808, )

def predict_model2(model, path, x_label, close_data):
	model.load_weights(path)
	result = model.predict(x_val_label, batch_size=parser['batch_size'], verbose=1, steps=None)
	close_predict = (result[:close_data[-3,-1]-1]*close_data[-3,1])+close_data[-3,0]
	tmp = (result[(close_data[-3,-1])-1:(close_data[-3,-1])+(close_data[-2,-1])-1]*close_data[-2,1])+close_data[-2,0]
	close_predict = np.append(close_predict,tmp)
	tmp = (result[(close_data[-3,-1])+(close_data[-2,-1])-1:]*close_data[-1,1])+close_data[-1,0]
	close_predict = np.append(close_predict,tmp)
	close_predict = close_predict[:,np.newaxis]	# �����͸� 1���� �ø���.
	save_graph(x_label, close_predict, 325, 1808, )

def split_data(x_data,norm_close_data, non_norm_close_data):
	leng = int(len(x_data)*0.9)

	dev_x_label = x_data[0]
	dev_norm_close = norm_close_data[0]
	
	val_x_lable = x_data[leng]
	val_non_norm_close = non_norm_close_data[leng]

	for i in range(1,len(x_data)):
		if i < leng:

			dev_x_label = np.concatenate((dev_x_label,x_data[i]))
			dev_norm_close = np.concatenate((dev_norm_close,norm_close_data[i]))

		elif i > leng:
			val_x_lable = np.concatenate((val_x_lable,x_data[i]))
			val_non_norm_close = np.concatenate((val_non_norm_close,non_norm_close_data[i]))

	return(dev_x_label, dev_norm_close, val_x_lable, val_non_norm_close)

if __name__ == '__main__':
	#yaml���� �ε�
	dir_yaml = '03_model_close_train.yaml'
	with open(dir_yaml, 'r', encoding='UTF8') as f_yaml:
		parser = yaml.load(f_yaml)

	filename=[]
	x_label = []
	normal_close = []
	non_norm_close = []
	close_data=[]

	for root, dirs, files in os.walk('./data'):
		for file in files:
			filename.append(file[:-5])

	for name in filename:
		data_temp = np.load('./data_label/'+name+'_data.npy')
		
		close_temp = []
	
		for i in data_temp[135:,4]:		# 34+100+1 -> 34������ ����� ��ǥ�� ��� ����, timestep 100, �Ϸ�� ���� 1
			close_temp.append(float (i))

		close_temp = np.array(close_temp)

		close_min = min(close_temp)
		close_max = max(close_temp)
		
		under = close_max - close_min		# ���� ����ȭ�� ����� ������ �ٽ� ����ϱ� ����
		close_data.append([int(close_min), int(under), int(len(close_temp))])

		close_temp = close_temp[:,np.newaxis]	# �����͸� 1���� �ø���.
		non_norm_close.append(close_temp)

	non_norm_close = np.array(non_norm_close)
	close_data = np.array(close_data)

	for name in filename:
		x_temp, close_temp = load_data('./data_label/'+name, 100)
		x_label.append(x_temp)
		normal_close.append(close_temp)

	x_label = np.array(x_label)
	normal_close = np.array(normal_close)
	
	x_dev_label, dev_norm_close, x_val_label, val_non_norm_close = split_data(x_label, normal_close, non_norm_close)
	
	model, m_name = get_model(argDic = parser['model'])

	#predict_model2(model,'C:/Users/thwjd/source/stock_predict/networks/18_predict_model001/20-0.0272-5422.6158.h5'
	#		   ,val_non_norm_close,close_data)
	#exit()

	save_dir = parser['save_dir'] + parser['name'] + '/'

	#���� ��� ���� ����(��) ����
	if not os.path.exists(save_dir):
		os.makedirs(save_dir)

	#���� ���� hyper-parameter���� �ؽ�Ʈ ���Ͽ� ����
	f_params = open(save_dir + 'f_params.txt', 'w')
	for k, v in parser.items():
		f_params.write('{}:\t{}\n'.format(k, v))
	f_params.write('DNN model params\n')
	for k, v in parser['model'].items():
		f_params.write('{}:\t{}\n'.format(k, v))
	f_params.write('model_name: %s\n'%m_name)
	f_params.close()

	with open(save_dir + 'summary.txt' ,'w+') as f_summary:
		model.summary(print_fn=lambda x: f_summary.write(x + '\n'))

	#�� optimizer �� objective funciton ����
	if parser['optimizer'] == 'SGD':
		optimizer = eval(parser['optimizer'])(lr=parser['lr'],  decay = parser['opt_decay'])
	elif parser['optimizer'] == 'Adam':
		optimizer = eval(parser['optimizer'])(lr=parser['lr'], decay = parser['opt_decay'], amsgrad = bool(parser['amsgrad']))
	elif parser['optimizer'] == 'RMSprop':
		optimizer = eval(parser['optimizer'])(lr=parser['lr'], decay = parser['opt_decay'])

	model.compile(loss = parser['loss_function'],optimizer = optimizer,metrics = ['accuracy'])

	f_eer = open(save_dir + 'eers.txt', 'w', buffering=1)	# epoch �� ���� ����� �ؽ�Ʈ ���� ����

	#�ѹ� epoch�� �������� �н� �� ���ϰ� ���� �����Ѵ�.
	for epoch in range(parser['epoch']):
		
		hist = model.fit(x_dev_label,dev_norm_close, batch_size = parser['batch_size'], epochs = 1, verbose=1)

		#�н��� �𵨷� validation_set�� ���Ѵ�.
		result = model.predict(x_val_label, batch_size=parser['batch_size'], verbose=1, steps=None)

		#�� ����� ������ȭ�Ͽ� ���� ������ ǥ���Ѵ�.
		close_predict = (result[:close_data[-3,-1]-1]*close_data[-3,1])+close_data[-3,0]
		tmp = (result[(close_data[-3,-1])-1:(close_data[-3,-1])+(close_data[-2,-1])-1]*close_data[-2,1])+close_data[-2,0]
		close_predict = np.append(close_predict,tmp)
		tmp = (result[(close_data[-3,-1])+(close_data[-2,-1])-1:]*close_data[-1,1])+close_data[-1,0]
		close_predict = np.append(close_predict,tmp)

		close_predict = close_predict[:,np.newaxis]	# �����͸� 1���� �ø���.
		
		#������ validation_set�� �� ������� ������ ���밪�� ���� ������� ����Ѵ�.
		val_mae = sum(abs(close_predict-val_non_norm_close))/len(close_predict)

		print('epoch: %d, val_mae: %f \n'%(int(epoch), val_mae))
		f_eer.write('epoch: %d, val_mae: %f \n'%(int(epoch), val_mae))

		#save_graph(non_norm_close[int(leng*0.9):], close_predict,epoch,val_mae ,save_dir)
		model.save_weights(save_dir + '%d-%.4f-%.4f.h5'%(epoch, hist.history['loss'][0], val_mae))
	f_eer.close()
		