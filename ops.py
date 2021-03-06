import math
import numpy as np 
import tensorflow as tf

from tensorflow.python.framework import ops

# from utils import *

class batch_norm(object):
    def __init__(self, data_format, epsilon=1e-5, momentum = 0.9, name="batch_norm"):
        with tf.variable_scope(name):
            self.epsilon  = epsilon
            self.momentum = momentum
            self.name = name
            self.data_format = data_format

    def __call__(self, x, train=True):
        return tf.contrib.layers.batch_norm(x,
                                            data_format=self.data_format,
                                            decay=self.momentum, 
                                            fused=True,
                                            updates_collections=None,
                                            epsilon=self.epsilon,
                                            scale=True,
                                            is_training=train,
                                            scope=self.name)

class generator_prior(object):
    def __init__(self, rand_gen, parameters):
        self.parameters = parameters
        self.rand_gen = rand_gen

    def __call__(self, shape):
        return self.rand_gen(self.parameters[0], self.parameters[1], size=shape)


def binary_cross_entropy(preds, targets, name=None):
    """Computes binary cross entropy given `preds`.

    For brevity, let `x = `, `z = targets`.  The logistic loss is

        loss(x, z) = - sum_i (x[i] * log(z[i]) + (1 - x[i]) * log(1 - z[i]))

    Args:
        preds: A `Tensor` of type `float32` or `float64`.
        targets: A `Tensor` of the same type and shape as `preds`.
    """
    eps = 1e-12
    with ops.op_scope([preds, targets], name, "bce_loss") as name:
        preds = ops.convert_to_tensor(preds, name="preds")
        targets = ops.convert_to_tensor(targets, name="targets")
        return tf.reduce_mean(-(targets * tf.log(preds + eps) +
                              (1. - targets) * tf.log(1. - preds + eps)))

def conv_cond_concat(x, y):
    """Concatenate conditioning vector on feature map axis."""
    x_shapes = x.get_shape()
    y_shapes = y.get_shape()
    return tf.concat(3, [x, y*tf.ones([x_shapes[0], x_shapes[1], x_shapes[2], y_shapes[3]])])

def conv2d(input_, output_dim, data_format,
           k_h=5, k_w=5, d_h=2, d_w=2, stddev=0.02,
           name="conv2d"):

    if data_format == "NHWC":
        in_channels = input_.get_shape()[-1]
        strides = [1, d_h, d_w, 1]
    else:
        in_channels = input_.get_shape()[1]
        strides = [1, 1, d_h, d_w]

    with tf.variable_scope(name):
        w = tf.get_variable('w', [k_h, k_w, in_channels, output_dim],
                            initializer=tf.truncated_normal_initializer(stddev=stddev))
        conv = tf.nn.conv2d(input_, w, strides=strides, padding='SAME', data_format=data_format)

        biases = tf.get_variable('biases', [output_dim], initializer=tf.constant_initializer(0.0))
        conv = tf.reshape(tf.nn.bias_add(conv, biases, data_format=data_format), conv.get_shape())

        return conv

def deconv2d(input_, output_shape, data_format,
             k_h=5, k_w=5, d_h=2, d_w=2, stddev=0.02,
             name="deconv2d", with_w=False):

    if data_format == "NHWC":
        in_channels = input_.get_shape()[-1]
        out_channels = output_shape[-1]
        strides = [1, d_h, d_w, 1]
    else:
        in_channels = input_.get_shape()[1]
        out_channels = output_shape[1]
        strides = [1, 1, d_h, d_w]

    with tf.variable_scope(name):
        w = tf.get_variable('w', [k_h, k_w, out_channels, in_channels],
                            initializer=tf.random_normal_initializer(stddev=stddev))
        deconv = tf.nn.conv2d_transpose(input_, w, output_shape=output_shape,
                strides=strides, data_format=data_format)

        biases = tf.get_variable('biases', [out_channels], initializer=tf.constant_initializer(0.0))
        deconv = tf.reshape(tf.nn.bias_add(deconv, biases, data_format=data_format), deconv.get_shape())

        if with_w:
            return deconv, w, biases
        else:
            return deconv
       

def lrelu(x, leak=0.2, name="lrelu"):
  return tf.maximum(x, leak*x)

def linear(input_, output_size, scope=None, stddev=0.02, bias_start=0.0, with_w=False, transpose_b=False):
    shape = input_.get_shape().as_list()

    if not transpose_b:
        w_shape = [shape[1], output_size]
    else:
        w_shape = [output_size, shape[1]]

    with tf.variable_scope(scope or "Linear"):
        matrix = tf.get_variable("Matrix", w_shape, tf.float32,
                                 tf.random_normal_initializer(stddev=stddev))
        bias = tf.get_variable("bias", [output_size],
            initializer=tf.constant_initializer(bias_start))
        if with_w:
            return tf.matmul(input_, matrix, transpose_b=transpose_b) + bias, matrix, bias
        else:
            return tf.matmul(input_, matrix, transpose_b=transpose_b) + bias
