import os

tag = 'celebA'
dataset = 'celebA'
image_size = 64
gen_updates = 1
epoch = 4
batch_size = 64
z_dist = 'normal'
data_format = 'NCHW'

command = 'python main.py --debug --dataset %s --image_size %i --output_size %i --is_crop True --is_train True ' \
          '--sample_dir samples_%s --checkpoint_dir checkpoint_%s --tensorboard_run %s ' \
          '--gen_updates %i --epoch %i --batch_size %i --z_dist %s --data_format %s'%(dataset, image_size, image_size, \
                                                         tag, tag, tag, gen_updates, epoch, batch_size, z_dist, data_format)

print command
os.system(command)
