from math import log10, sqrt
from pathlib import Path
import cv2
import ffmpeg
import numpy as np
import matplotlib.pyplot as plt
import statistics
  
def PSNR(original, compressed): 
    mse = np.mean((original - compressed) ** 2) 
    if(mse == 0):  # MSE is zero means no noise is present in the signal . 
                  # Therefore PSNR have no importance. 
        return 100
    max_pixel = 255.0
    psnr = 20 * log10(max_pixel / sqrt(mse)) 
    return psnr 

def main():
    opt_psnr = []
    default_psnr = []
    project_path = "/Users/menghua/Research/TestX264/"
    comparison_video_suffix = "opt_vbv_1"
    comparison_video_suffix_default = "default_vbv_15"
    input_frames_directory = f"{project_path}input_frames/"
    comparison_frames_directory = f"{project_path}comparison_{comparison_video_suffix}/"
    comparison_frames_directory_default = f"{project_path}comparison_{comparison_video_suffix_default}/"
    
    if (not Path(comparison_frames_directory).exists()):
        comparison_video_path = f"{project_path}result/{comparison_video_suffix}.mkv"
        Path(comparison_frames_directory).mkdir(parents=True, exist_ok=True)
        (
            ffmpeg.input(comparison_video_path)
            .output(f"{comparison_frames_directory}output_%04d.png")
            .run()
        )
    if (not Path(comparison_frames_directory_default).exists()):
        comparison_video_path_default = f"{project_path}result/{comparison_video_suffix_default}.mkv"
        Path(comparison_frames_directory_default).mkdir(parents=True, exist_ok=True)
        (
            ffmpeg.input(comparison_video_path_default)
            .output(f"{comparison_frames_directory_default}output_%04d.png")
            .run()
        )

    for i in range(1, 479):
        original = cv2.imread(f"{input_frames_directory}input_{i:04d}.png") 
        compressed = cv2.imread(f"{comparison_frames_directory}output_{i:04d}.png", 1)
        compressed_default = cv2.imread(f"{comparison_frames_directory_default}output_{i:04d}.png", 1)
        value = PSNR(original, compressed)
        opt_psnr.append(value)
        value2 = PSNR(original, compressed_default)
        default_psnr.append(value2)
        print(f"Frame {i} opt PSNR value is {value} dB, default PSNR value is {value2} dB")

    print(f"Average PSNR value is {statistics.mean(opt_psnr)} dB")
    print(f"Average default PSNR value is {statistics.mean(default_psnr)} dB")
    time = np.arange(opt_psnr.__len__())
    plt.plot(time, opt_psnr, label = "opt_psnr")  # Plot the chart
    plt.plot(time, default_psnr, label = "default_psnr")  # Plot the chart
    plt.legend()
    plt.show()  # display
       
if __name__ == "__main__": 
    main() 