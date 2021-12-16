import numpy as np
import os
import ipywidgets as ui
from IPython.display import display
import time
import av
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import VideoFileClip
from tqdm import tqdm
import os

def rgb2gray(rgb):

    r, g, b = rgb[:,:,0], rgb[:,:,1], rgb[:,:,2]
    gray = 0.2989 * r + 0.5870 * g + 0.1140 * b

    return gray

#Rescale image to between 0 and 1. 
def rescale(arr):
    return arr.astype(float) / 255.
    #return arr/(np.max(arr)-np.min(arr))

def get_center_K_frames(filename, K):
    container = av.open(filename)
    frames = np.array([np.array(frame.to_image()) for frame in container.decode(video=0) ])
    strt_idx = (len(frames) // 2) - (K // 2)
    end_idx = (len(frames) // 2) + (K // 2)
    return frames[strt_idx: end_idx + 1][:K]
 

def get_sliced_movie(filenames, numFrames, slc = [0, 720, 0, 1280], dataDir = "./data"):
    frames_sliced = np.zeros((len(filenames), numFrames, slc[1]-slc[0], slc[3]-slc[2], 3))
    for j,filename in enumerate(filenames):
        container = av.open(os.path.join(dataDir, filename))
        frames = np.array([np.array(frame.to_image()) for frame in container.decode(video=0) ])
        frames_sliced[j, : ,: ,:, :] = frames[-(numFrames):,slc[0]:slc[1],slc[2]:slc[3],:]
    return np.array(frames_sliced)

    
# copied from: https://stackoverflow.com/questions/48056345/jupyter-lab-browsing-the-remote-file-system-inside-a-notebook
class PathSelector():

    def __init__(self,start_dir,select_file=True):
        self.file        = None 
        self.select_file = select_file
        self.cwd         = start_dir
        self.select      = ui.SelectMultiple(options=['init'],value=(),rows=10,description='') 
        self.accord      = ui.Accordion(children=[self.select]) 

        self.accord.selected_index = None # Start closed (showing path only)
        self.refresh(self.cwd)
        self.select.observe(self.on_update,'value')

    def on_update(self,change):
        if len(change['new']) > 0:
            self.refresh(change['new'][0])

    def refresh(self,item):
        path = os.path.abspath(os.path.join(self.cwd,item))

        if os.path.isfile(path):
            if self.select_file:
                self.accord.set_title(0,path)  
                self.file = path
                self.accord.selected_index = None
            else:
                self.select.value = ()

        else: # os.path.isdir(path)
            self.file = None 
            self.cwd  = path

            # Build list of files and dirs
            keys = ['[..]']; 
            for item in os.listdir(path):
                if item[0] == '.':
                    continue
                elif os.path.isdir(os.path.join(path,item)):
                    keys.append('['+item+']'); 
                else:
                    keys.append(item); 

            # Sort and create list of output values
            keys.sort(key=str.lower)
            vals = []
            for k in keys:
                if k[0] == '[':
                    vals.append(k[1:-1]) # strip off brackets
                else:
                    vals.append(k)

            # Update widget
            self.accord.set_title(0,path)  
            self.select.options = list(zip(keys,vals)) 
            with self.select.hold_trait_notifications():
                self.select.value = ()


def get_movie_duration(filename):
    clip = VideoFileClip(filename)
    return clip.duration

def extract_clip(filename, start=0, end=10, savename = ""):
    if not savename:
        savename = "tmp"+str(np.random.randint(1000))+".webm"
    ffmpeg_extract_subclip(filename, start, end, targetname=savename)
    return savename

class ImageSliceViewer3D:
    """ 
    ImageSliceViewer3D is for viewing volumetric image slices in jupyter or
    ipython notebooks. 
    
    User can interactively change the slice plane selection for the image and 
    the slice plane being viewed. 

    Argumentss:
    Volume = 3D input image
    figsize = default(8,8), to set the size of the figure
    cmap = default('plasma'), string for the matplotlib colormap. You can find 
    more matplotlib colormaps on the following link:
    https://matplotlib.org/users/colormaps.html
    
    """
    
    def __init__(self, volume, figsize=(15,15)):
        self.volume = rescale(volume)
        self.figsize = figsize
        
        # Call to view a slice within the selected slice plane
        ipyw.interact(self.plot_slice, 
            z=ipyw.IntText(continuous_update=False, 
            description='Image Slice:'))
   
        
    def plot_slice(self, z):
        # Plot slice for the given plane and slice
        fig, ax = plt.subplots(figsize = self.figsize)
        vmin, vmax = 0.0, 1.0
        image = self.volume[z,:,:].transpose(1,0)
        ax.imshow(self.volume[z,:,:].transpose(1,0), origin='lower',cmap='gray').set_clim(vmin,vmax)