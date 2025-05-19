import os
from modelscope import snapshot_download

os.makedirs('./model')
snapshot_download('iic/speech_campplus_sv_zh-cn_16k-common', cache_dir='./model')
snapshot_download('iic/speech_fsmn_vad_zh-cn-16k-common-pytorch', cache_dir='./model')
snapshot_download('iic/punc_ct-transformer_zh-cn-common-vocab272727-pytorch', cache_dir='./model')
snapshot_download('iic/speech_seaco_paraformer_large_asr_nat-zh-cn-16k-common-vocab8404-pytorch', cache_dir='./model')