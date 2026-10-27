import os
import sys
import subprocess
from pathlib import Path

ROOT=Path(__file__).resolve().parent
DATA=Path(os.environ.get('VOCAL_REMOVER_DATA_DIR', str(ROOT/'data'))).resolve()
MODELS=Path(os.environ.get('VOCAL_REMOVER_MODELS_DIR', str(ROOT/'models'))).resolve()
os.environ['NUMBA_CACHE_DIR']=str(DATA/'cache'/'numba')
os.environ['MPLCONFIGDIR']=str(DATA/'cache'/'matplotlib')
os.environ['XDG_CACHE_HOME']=str(DATA/'cache')
import torch
torch.set_num_threads(min(6, os.cpu_count() or 4))
from audio_separator.separator import Separator

folder=Path(sys.argv[1]).resolve()
model=sys.argv[2]
start_seconds=int(sys.argv[3]) if len(sys.argv)>3 else 0
preview_seconds=int(sys.argv[4]) if len(sys.argv)>4 else 0
original_blend=int(sys.argv[5]) if len(sys.argv)>5 else 0
source=next(folder.glob('input.*'))
wav=folder/'source.wav'
decode=['ffmpeg','-nostdin','-v','error','-y','-ss',str(start_seconds),'-i',str(source)]
if preview_seconds:
    decode += ['-t',str(preview_seconds)]
subprocess.run(decode+['-map','0:a:0','-ac','2','-ar','44100',str(wav)],check=True)
separator=Separator(model_file_dir=str(MODELS),output_dir=str(folder),output_format='WAV',
                    output_single_stem='Instrumental',use_soundfile=True,
                    mdxc_params={'segment_size':256,'override_model_segment_size':False,
                                 'batch_size':1,'overlap':2,'pitch_shift':0})
separator.torch_device=torch.device('cpu')
separator.onnx_execution_provider=['CPUExecutionProvider']
separator.load_model(model_filename=model)
files=separator.separate(str(wav),{'Instrumental':'backing'})
if original_blend:
    import numpy as np
    import soundfile as sf
    original,sr=sf.read(wav,always_2d=True)
    processed,output_sr=sf.read(folder/'backing.wav',always_2d=True)
    if sr!=output_sr or original.shape!=processed.shape:
        raise ValueError('Cannot blend audio with mismatched sample rates or dimensions.')
    blend=original_blend/100
    restored=(1-blend)*processed+blend*original
    peak=np.max(np.abs(restored))
    if peak>0.95:
        restored*=0.95/peak
    sf.write(folder/'backing.wav',restored,sr,subtype='PCM_16')
wav_result=folder/'result.wav'
(folder/'backing.wav').replace(wav_result)
# Export both formats. The WAV is useful when the user wants to continue mixing
# and avoids adding another lossy encode to an already processed track.
result=folder/'result.mp3'
subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-i',str(wav_result),'-codec:a','libmp3lame',
                '-b:a','320k',str(result)],check=True)
for path in [source,wav]:
    path.unlink(missing_ok=True)
print('COMPLETE',flush=True)
