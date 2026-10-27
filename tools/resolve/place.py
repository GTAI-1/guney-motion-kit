# Put a rendered graphics overlay (a .mov with transparency) on top of the timeline that is open in DaVinci Resolve.
# Usage (from the project folder, Resolve open with your edit): python3 ../../tools/resolve/place.py renders/overlay.mov [--at 00:00:10:00]
#   --at   where the overlay starts on the timeline (timecode); default: the timeline's start
# It imports the file into the Media Pool, adds a new video track above the others and puts the clip there. Your footage is
# not touched. Resolve must allow scripting: Preferences > System > General > External scripting using: Local.
import os, sys
def resolve_app():
    paths = {'darwin': '/Library/Application Support/Blackmagic Design/DaVinci Resolve/Developer/Scripting/Modules',
             'win32': os.path.expandvars(r'%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting\Modules'),
             'linux': '/opt/resolve/Developer/Scripting/Modules'}
    sys.path.append(paths.get(sys.platform, paths['linux']))
    import DaVinciResolveScript as dvr
    return dvr.scriptapp('Resolve')
def frames(tc, fps):
    h, m, s, f = [int(x) for x in tc.replace(';', ':').split(':')]; fr = round(fps)
    return ((h * 60 + m) * 60 + s) * fr + f
args = sys.argv[1:]
if not args: print(__doc__ or 'usage: place.py <file.mov> [--at HH:MM:SS:FF]'); sys.exit(1)
path = os.path.abspath(args[0]); at = args[args.index('--at') + 1] if '--at' in args else None
r = resolve_app()
if not r: print('Could not reach Resolve. Is it open, with external scripting set to Local?'); sys.exit(1)
proj = r.GetProjectManager().GetCurrentProject(); tl = proj.GetCurrentTimeline()
if not tl: print('Open the timeline you want the graphics on, then run this again.'); sys.exit(1)
mp = proj.GetMediaPool(); clip = mp.ImportMedia([path])[0]
tl.AddTrack('video'); track = tl.GetTrackCount('video')
start = tl.GetStartFrame() + (frames(at, float(tl.GetSetting('timelineFrameRate'))) - frames(tl.GetStartTimecode(), float(tl.GetSetting('timelineFrameRate'))) if at else 0)
item = mp.AppendToTimeline([{'mediaPoolItem': clip, 'recordFrame': start, 'trackIndex': track, 'mediaType': 1}])
print(('Placed %s on video track %d.' % (os.path.basename(path), track)) if item and item[0] else 'Resolve did not accept the clip: check the file and the timeline.')
