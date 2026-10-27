# Black-frame and one-frame-pop scan of a render. Usage (from the project folder): python3 ../../tools/qa/scan.py <section>/<name>   (reads renders/<section>/<name>.mp4)
import subprocess, numpy as np, sys, json
def frames(path, w=240, h=135):
    raw = subprocess.run(['ffmpeg','-v','error','-i',path,'-vf',f'scale={w}:{h},format=gray','-f','rawvideo','-'],capture_output=True).stdout
    return np.frombuffer(raw,np.uint8).reshape(-1,h,w).astype(np.float32)
for name in sys.argv[1:]:
    f = frames(f'renders/{name}.mp4'); n = len(f)
    d = np.abs(np.diff(f,axis=0)).mean(axis=(1,2)); mean = f.mean(axis=(1,2))
    f0 = f[0]; blank = f0.std() < 6
    jumps = [(i+1, round(float(v),1)) for i,v in enumerate(d) if v > 18]
    black = [i for i,m in enumerate(mean) if m < 8]
    # one-frame pops: frame differs from both neighbours while neighbours agree
    pops = [i for i in range(1,n-1) if np.abs(f[i]-f[i-1]).mean()>12 and np.abs(f[i]-f[i+1]).mean()>12 and np.abs(f[i-1]-f[i+1]).mean()<6]
    print(json.dumps({'file':name,'frames':n,'frame0_blank':bool(blank),'frame0_std':round(float(f0.std()),2),'hard_jumps(>18)':jumps,'black_frames':black[:10],'one_frame_pops':pops}))
