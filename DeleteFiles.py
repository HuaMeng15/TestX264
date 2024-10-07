from pathlib import Path

def main():
    file_names = ["Lecture720", "Lecture1", "Lecture2", "Lecture3", "Lecture4", "Sports", "Sport2", "Animation1", "Animation2", "CoverSong", "Gaming"]
    bitrate_configs = ["static", "3000-1500", "3000-300", "3000-50"]
    file_suffixs = ["default", "opt"]
    project_path = "/Users/menghua/Research/TestX264/"
    
    for file_name in file_names:
        for bitrate_config in bitrate_configs:
            for file_suffix in file_suffixs:
                result_path = f"{project_path}result/{file_name}_{bitrate_config}/"
                psnr_file = f"{result_path}{file_suffix}_psnr.csv"
                display_psnr_file = f"{result_path}{file_suffix}_display_psnr.csv"
                if (Path(psnr_file).exists()):
                    Path(psnr_file).unlink()
                if (Path(display_psnr_file).exists()):
                    Path(display_psnr_file).unlink()
            
       
if __name__ == "__main__": 
    main() 