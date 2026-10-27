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
torch.set_num_threads(4)
from audio_separator.separator import Separator

folder=Path(sys.argv[1]).resolve()
model=sys.argv[2]
source=next(folder.glob('input.*'))
wav=folder/'source.wav'
subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-i',str(source),'-map','0:a:0','-ac','2','-ar','44100',str(wav)],check=True)
separator=Separator(model_file_dir=str(MODELS),output_dir=str(folder),output_format='WAV',
                    output_single_stem='Instrumental',use_soundfile=True)
separator.torch_device=torch.device('cpu')
separator.onnx_execution_provider=['CPUExecutionProvider']
separator.load_model(model_filename=model)
files=separator.separate(str(wav),{'Instrumental':'backing'})
result=folder/'result.mp3'
subprocess.run(['ffmpeg','-nostdin','-v','error','-y','-i',str(folder/'backing.wav'),'-codec:a','libmp3lame',
                '-b:a','320k',str(result)],check=True)
# Keep only the user's result and the diagnostic log after successful processing.
for path in [source,wav,folder/'backing.wav']:
    path.unlink(missing_ok=True)
print('COMPLETE',flush=True)
