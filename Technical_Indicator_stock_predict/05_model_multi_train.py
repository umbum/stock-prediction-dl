#-*- coding: cp949 -*-
#-*- coding: utf-8 -*- 

# ����� �����͸� �ҷ��� �н��� �����ϰ� �ϱ� ���� ����ȭ ��Ų��.
# ����ȭ�� �����͸� �̿��Ͽ� ���� ���� �н���Ų��.
# �� epoch ���� �н� �� ���Ͽ� ���� �����Ѵ�.
# ������ ����� ���ÿ� �н��ϴ� ��

import numpy as np
from TI_GRU_multi import get_model
from sklearn.preprocessing import MinMaxScaler
import tensorflow as tf
from keras.optimizers import *
from keras.models import Model
from sklearn.metrics import roc_curve
from scipy.optimize import brentq
from scipy.interpolate import interp1d
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
	y_temp = np.load(stock_name+'_y_label.npy')
	
	x_temp = normalize_data(x_temp[34:-1],12)			# 34��° ������ ���� �����Ͱ� ����, �����������ʹ� ���� �� �� ���⿡ ����
	close = normalize_data(data_temp[35+time_step:, 4],1)			# time_stpe���� 35��° ���� ���� ����

	
	x_label = []
	y_label = []

	for index in range(len(x_temp) - time_step): 
		x_label.append(x_temp[index: index + time_step])

	for y in y_temp[35+time_step:]:		# �ְ��� ��� �϶��� one hot vector�� ǥ��
		
		y = float(y)
		if y >0:
			y_label.append(1)
		else :
			y_label.append(0)

	return (np.array(x_label), np.array(y_label),np.array(close))

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

def updown_error(model,data_x,data_y):
	y_score = []

	results = model.predict(data_x)

	
	for i in range(len(results)):
		if results[i][1]>0.5:
			y_score.append(1)
		else:
			y_score.append(0)
	print(data_y[:100])
	print(y_score[:100])
	print(sum(abs(data_y-y_score)))
	print(len(y_score))
	err = sum(abs(data_y-y_score))/len(data_y)
	#fpr, tpr, thresholds = roc_curve(data_y, y_score, pos_label=1)
	#eer = brentq(lambda x: 1. - x - interp1d(fpr, tpr)(x), 0., 1.)

	return err

def predict_model(model, path, x_label, under, close_min ):
	model.load_weights(path)
	result = model.predict(x_val_label, batch_size=parser['batch_size'], verbose=1, steps=None)
	close_predict = (result*under)+close_min
	save_graph(x_label, close_predict, 325, 1808, )

if __name__ == '__main__':

	#yaml���� �ε�
	_abspath = os.path.abspath(__file__)
	dir_yaml = os.path.splitext(_abspath)[0] + '.yaml'
	with open(dir_yaml, 'r', encoding='UTF8') as f_yaml:
		parser = yaml.load(f_yaml)
	
	data_temp = np.load('sk_data.npy')
	non_norm_close = []
	for i in data_temp[135:,4]:		# 34+100+1 -> 34������ ����� ��ǥ�� ��� ����, timestep 100, �Ϸ�� ���� 1
		non_norm_close.append(float (i))
	
	non_norm_close = np.array(non_norm_close)
	
	non_norm_close = non_norm_close[:,np.newaxis]	# �����͸� 1���� �ø���.
	
	close_min = min(non_norm_close)
	close_max = max(non_norm_close)
	
	under = close_max - close_min		# ���� ����ȭ�� ����� ������ �ٽ� ����ϱ� ����

	x_label, y_label, normal_close = load_data('sk',100)	
	
	leng = len(x_label)			
	
	# development_set�� 0.9 validation_set�� 0.1�� �����.
	x_dev_label = x_label[:int(leng*0.9),:,:]	
	x_val_label = x_label[int(leng*0.9):,:,:]
	y_dev_label = y_label[:int(leng*0.9)]	
	y_val_label = y_label[int(leng*0.9):]
	close_dev = normal_close[:int(leng*0.9),:]
	close_val = normal_close[int(leng*0.9):,:]

	model, m_name = get_model(argDic = parser['model'])

	#predict_model(model,'C:/Users/thwjd/source/stock_predict/networks/sk_predict_model010/1012-0.0103-1860.3714.h5'
	#		   ,non_norm_close[int(leng*0.9):],under,close_min)
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

	
	model.compile(loss = {'price_out':parser['price_loss'],'binary_out':parser['binary_loss']},
			   loss_weights = {'price_out':1,'binary_out':1},
			   optimizer = optimizer,metrics = ['accuracy'])

	f_eer = open(save_dir + 'eers.txt', 'w', buffering=1)	# epoch �� ���� ����� �ؽ�Ʈ ���� ����

	#�ѹ� epoch�� �������� �н� �� ���ϰ� ���� �����Ѵ�.
	for epoch in range(parser['epoch']):
		
		#model.fit(x_dev_label,close_temp[:int(leng*0.9),:], batch_size = 100, epochs = 1, verbose=1)
		hist = model.fit(x_dev_label,[close_dev,y_dev_label], batch_size = parser['batch_size'], epochs = 1, verbose=1)
		price_model = Model(inputs=model.get_layer('input_1').input, outputs=model.get_layer('price_out').output)
		binary_model = Model(inputs=model.get_layer('input_1').input, outputs=model.get_layer('binary_out').output)

		binary_error = updown_error(binary_model, x_val_label,y_val_label)
		
		#�н��� �𵨷� validation_set�� ���Ѵ�.
		result = price_model.predict(x_val_label, batch_size=parser['batch_size'], verbose=1, steps=None)
	
		#�� ����� ������ȭ�Ͽ� ���� ������ ǥ���Ѵ�.
		close_predict = (result*under)+close_min
		
		#������ validation_set�� �� ������� ������ ���밪�� ���� ������� ����Ѵ�.
		#val_mae = sum(abs(result-close_temp[int(leng*0.9):,:]))/len(result)
		close_error = sum(abs(close_predict-non_norm_close[int(leng*0.9):]))/len(close_predict)
		
		print('epoch: %d, binary_error: %f, close_error: %f \n'%(int(epoch), binary_error, close_error))
		f_eer.write('epoch: %d, binary_error: %f, close_error: %f \n'%(int(epoch), binary_error, close_error))

		save_graph(non_norm_close[int(leng*0.9):], close_predict, epoch, close_error, save_dir)
		model.save_weights(save_dir + '%d-%.4f-%.4f-%.4f.h5'%(epoch, hist.history['loss'][0], binary_error, close_error))
	f_eer.close()
		