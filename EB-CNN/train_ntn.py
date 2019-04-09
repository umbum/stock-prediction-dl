from __future__ import print_function

import random
import sys
import math
import numpy as np
import scipy.stats as stats

from sklearn.datasets import load_digits
from keras import backend as K
from keras.engine.topology import Layer
from keras.optimizers import SGD
from keras.layers import Dense
from keras.layers import subtract
from keras.layers import add
from keras.layers import Input
from keras.models import Model, load_model
from keras.utils import CustomObjectScope

class NeuralTensorLayer(Layer):
  def __init__(self, output_dim, input_dim=None, **kwargs):
    self.output_dim = output_dim #k
    self.input_dim = input_dim   #d
    if self.input_dim:
      kwargs['input_shape'] = (self.input_dim,)
    super(NeuralTensorLayer, self).__init__(**kwargs)


  def build(self, input_shape):
    print("output shape: ",self.compute_output_shape(input_shape))
    mean = 0.0
    std = 1.0
    # T : k*d*d
    k = self.output_dim
    d = self.input_dim
    initial_T_values = stats.truncnorm.rvs(-2 * std, 2 * std, loc=mean, scale=std, size=(k,d,d))
    initial_W_values = stats.truncnorm.rvs(-2 * std, 2 * std, loc=mean, scale=std, size=(k,2*d))
    self.T1 = K.variable(initial_T_values, name='T1')
    self.T2 = K.variable(initial_T_values, name='T2')
    self.T3 = K.variable(initial_T_values, name='T3')
    self.W = K.variable(initial_W_values, name='W')
    self.b = K.zeros((k,1),name='b')
    self.trainable_weights = [self.T1, self.T2, self.T3, self.W, self.b]


  def call(self, inputs, mask=None):
    if type(inputs) is not list or len(inputs) <= 3:
      raise Exception('BilinearTensorLayer must be called on a list of tensors '
                      '(at least 4). Got: ' + str(inputs))


    # e1, p, e2 are each shape (?,d)
    # '?' is batch size
    e1 = inputs[0]
    p = inputs[1]
    e2 = inputs[2]
    er = inputs[3]
    batch_size = K.shape(e1)[0]
    d = self.input_dim
    k = self.output_dim
    bs = np.int(K.get_value(batch_size))
    print(bs," = bs")

    u = ntn( K.reshape(ntn(e1, p, self.W, self.T1, self.b, d, k , batch_size),(bs,d)),
             K.reshape(ntn(p, e2, self.W, self.T2, self.b , d, k , batch_size),(bs,d)), self.W, self.T3, self.b , d, k , batch_size)
    ur = ntn(K.reshape(ntn(er, p, self.W, self.T1, self.b, d, k, batch_size),(bs,d)),
            K.reshape(ntn(p, e2, self.W, self.T2, self.b, d, k, batch_size),(bs,d)), self.W, self.T3, self.b, d, k, batch_size)
    result = K.concatenate([K.reshape(u,(1,d,bs)) ,K.reshape(ur,(1,d,bs))],axis =0)
    #print(result,":result")
    return result


  def compute_output_shape(self, input_shape):
    # print (input_shape)
    batch_size = input_shape[0][0]
    return (batch_size, self.output_dim)

  def get_config(self):
    config = {
      'output_dim': self.output_dim,
      'input_dim': self.input_dim
    }
    base_config = super(NeuralTensorLayer, self).get_config()
    return dict(list(base_config.items()) + list(config.items()))

def ntn(e1, e2, W, T, b , d, k , batch_size ):
  bs = np.int(K.get_value(batch_size))
  #'?' is batch size
  #print(e1,":e1") #(?,d)
  #print(W, ":W")  #(k, 2*d)
  #print(K.reshape(K.concatenate([e1, e2]),(2*d,1)), ":e1+e2") #(2*d, ?)

  feed_forward_product = K.dot(W, K.reshape(K.concatenate([e1, e2]),(2*d,bs)))  # (k,?)
  #print(feed_forward_product, ":ffp")


  #print(K.dot( K.reshape(e1[0],(1,64)), T[0]),":K.dot( K.reshape(e1[0],(1,64)), T[0])") #(1,64)
  #print( K.transpose(e2[0]) , ": K.transpose(e2[0])") #(64, )
  bilinear_tensor_products = K.dot(K.dot( K.reshape(e1[0],(1,64)), T[0]), K.reshape(K.transpose(e2[0]),(64,1)))
  #print(bilinear_tensor_products, "!!")  #(1,1)


  # iterate 'bs' times for batch processing
  for j in range(bs)[1:]:
    btp = K.dot(K.dot( K.reshape(e1[j],(1,64)), T[0]), K.reshape(K.transpose(e2[j]),(64,1)))
    bilinear_tensor_products = K.concatenate([bilinear_tensor_products, btp])
    #print(bilinear_tensor_products, "??")

  #interate for 'K' size
  for i in range(k)[1:]:
    btpt =  K.dot(K.dot( K.reshape(e1[0],(1,64)), T[i]), K.reshape(K.transpose(e2[0]),(64,1)))
    for j in range(bs)[1:]:
      btp =  K.dot(K.dot( K.reshape(e1[j],(1,64)), T[i]), K.reshape(K.transpose(e2[j]),(64,1)))
      btpt = K.concatenate([btpt, btp])
    #print(btpt, "??")

    bilinear_tensor_products = K.concatenate([bilinear_tensor_products, btpt], axis=0)
  #print(bilinear_tensor_products, ":final btp")  # (?,k)

  #print(add([bilinear_tensor_products, feed_forward_product]),":add([bilinear_tensor_products, feed_forward_product])")
  #print(K.tf.broadcast_to(b, [k, bs]),":K.tf.broadcast_to(b, [k, bs])")
  r = K.tanh(
    add([add([bilinear_tensor_products, feed_forward_product]), K.tf.broadcast_to(b, [k, bs])]))
  #print(r, ":r")

  return r

# variation of socher's contrastive max-margin objective function = xiao ding paper loss
def custom_loss(varis,oup,bs):
  def contrastive_loss(y_true, y_pre):
    y_pre = K.print_tensor(y_pre, message="Value of u,ur")

    #print(y_pre[1, :],":y_pre[1, :]")
    temp1 = K.tf.maximum(subtract([y_pre[1, :, 0], y_pre[0, :, 0]]) + 1, 0)
    temp1 = K.print_tensor(temp1, message="temp1:1th batch")
    temp1 = K.tf.reduce_sum(temp1)
    temp1 = K.print_tensor(temp1, message="temp1:1th batch")
    for i in range(1,bs):
      temp1s = K.tf.maximum(subtract([y_pre[1,:,i],y_pre[0,:,i]]) + 1, 0)
      temp1s = K.print_tensor(temp1s, message="temp1:%dth batch"%(i+1))
      temp1s = K.tf.reduce_sum(temp1s)
      temp1 = K.concatenate([K.reshape(temp1,(1,i)), K.reshape(temp1s,(1,1))])
      temp1 = K.print_tensor(temp1, message="temp1:after calc %dth batch" % (i+1))

    for i in range(0, 5):
      #print(varis[i])
      varis[i] = K.print_tensor(varis[i], message="Value of varis%d"%(i))
    temp2 = []
    for i in range(0,5):
      temp2.append(K.tf.reduce_sum(K.tf.square(varis[i])))
    #print(temp2)
    temp2 = K.print_tensor(temp2, message="Value of temp2")
    temp2 = K.tf.reduce_sum(temp2)
    #print(temp2)
    temp2 = K.print_tensor(temp2, message="Value of temp2")
    temp = temp1 + (([0.000001]) * temp2)
    temp = K.print_tensor(temp, message="Value of temp1+temp2*0.000001")



    return temp
  return contrastive_loss

def get_data(bs):
  digits = load_digits()
  L = int(math.floor(digits.data.shape[0] * 0.15))
  L = L - divmod(L,4*bs)[1]
  X_train = digits.data[:L]
  y_train = digits.target[:L]
  X_test = digits.data[L + 1:]
  y_test = digits.target[L + 1:]
  return X_train, y_train, X_test, y_test

def main():

  inp = 64
  oup = 64 # must be multiple of 2
  bs = 1

  input1 = Input(shape=(inp,), batch_shape=(bs,inp) ,dtype='float32')
  input2 = Input(shape=(inp,), batch_shape=(bs,inp) ,dtype='float32')
  input3 = Input(shape=(inp,), batch_shape=(bs,inp) ,dtype='float32')
  input4 = Input(shape=(inp,), batch_shape=(bs,inp) ,dtype='float32')
  btp= NeuralTensorLayer(output_dim=oup, input_dim=inp)([input1, input2, input3, input4])


  model = Model(input=[input1, input2, input3, input4], output=[btp])

  sgd = SGD(lr=0.0001, decay=1e-6, momentum=0.9, nesterov=True)
  model.compile(loss=custom_loss(model.trainable_weights,oup,bs), optimizer=sgd)
  X_train, Y_train, X_test, Y_test = get_data(bs)
  X_train = X_train.astype(np.float32)
  Y_train = Y_train.astype(np.float32)
  X_test = X_test.astype(np.float32)
  Y_test = Y_test.astype(np.float32)


  model.fit([X_train*(random.getrandbits(2)/1000), X_train*(random.getrandbits(2)/1000),
             X_train*(random.getrandbits(2)/1000), X_train*(random.getrandbits(2)/1000)],Y_train , epochs=1, batch_size=bs)
  score = model.evaluate([X_test*(random.getrandbits(2)/1000), X_test*(random.getrandbits(2)/1000),
                          X_test*(random.getrandbits(2)/1000), X_test*(random.getrandbits(2)/1000)], Y_test, batch_size=bs)
  print(score)

  model.save("ntn.h5")
  print("Save model: 'ntn.h5'")


if __name__ == "__main__" :
  main()



