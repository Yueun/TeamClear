import os, sys, glob, re, argparse
import numpy as np
import tensorflow as tf

from lib._psnr import psnr
from lib._model import model
from lib._rgb2ycbcr import *

from scipy.misc import imread
from scipy.misc import imresize

f_size = 96
s_epoch = 27

DATA_PATH = "_uploads/extracts/"
result_path_dir = "_uploads/result/"
file_list = os.listdir(DATA_PATH)
file_list.sort()

def test_with_sess(epoch, ckpt_path, data_path,sess):
  psnr_list = []
  for i in range(2):
    psnr_list.append([])
  for i in range(3):
    psnr_list[0].append([])
    psnr_list[1].append([])
  saver.restore(sess, ckpt_path)
  for i, item in enumerate(file_list):
    file_name = os.path.splitext(item)
    img_raw = imread(DATA_PATH+item)
    width = img_raw.shape[1]
    height = img_raw.shape[0]
    if len(img_raw.shape) == 3:
      im_gt_ycbcr = np.round(rgb2ycbcr(img_raw)).astype('uint8')
      im_gt_ycbcr = cropping(im_gt_ycbcr,height,width)
      img_raw = im_gt_ycbcr[:,:,0]/255.0
      is_gray = False
    elif len(img_raw.shape) == 2:
      im_gt_ycbcr = 0
      img_raw = img_raw/255.0
      is_gray = True
    for x in range(4,5):#About scale X2, X3, X4
      im_gt_y = imresize(imresize(img_raw, 1/x, interp='bicubic', mode='F'), [img_raw.shape[0], img_raw.shape[1]], interp='bicubic', mode='F')
      result_y = sess.run([output_tensor], feed_dict={input_tensor: np.resize(im_gt_y, (1, im_gt_y.shape[0], im_gt_y.shape[1], 1)), keep_prob: 1.0})

      result_y = np.resize(result_y, (im_gt_y.shape[0], im_gt_y.shape[1]))
      result_y = result_y.clip(16/255, 235/255)
      image = colorize(result_y, im_gt_ycbcr, is_gray)
      image.save(result_path_dir+file_name[0]+"X"+str(x)+file_name[1])

      psnr_list[0][x - 2].append(psnr(result_y, img_raw, x))
      psnr_list[1][x - 2].append(psnr(im_gt_y, img_raw, x))
  print("VDSR Success")

if __name__ == '__main__':
  model_list = sorted(glob.glob("./checkpoints/epoch_*"))
  model_list = [fn for fn in model_list if not os.path.basename(fn).endswith("meta")]
  model_list = [fn for fn in model_list if not os.path.basename(fn).endswith("index")]
  if os.path.exists(result_path_dir):
    files = [f for f in os.listdir(result_path_dir)]
    for f in files:
      os.remove(str(result_path_dir+f))
  else:
    os.makedirs(result_path_dir)

  with tf.Session() as sess:
    input_tensor = tf.placeholder(tf.float32, shape=(1, None, None, 1))
    keep_prob = tf.placeholder("float")
    shared_model = tf.make_template('shared_model', model)
    output_tensor, weights 	= shared_model(input_tensor, f_size, keep_prob)
    saver = tf.train.Saver(weights)
    tf.global_variables_initializer().run()
    for model_ckpt in model_list:#read only .data file (started index::step)
      model_ckpt = model_ckpt.split(".data")[0]
      epoch = int(model_ckpt.split('epoch_')[-1].split('(')[0])
      if epoch == s_epoch:
        print("Testing ", model_ckpt)
        test_with_sess(epoch, model_ckpt, DATA_PATH,sess)
