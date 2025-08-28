import os

def read_data_from_file(file, count, data_lists, seperator):
    lines = open(file,'r').read().split('\n')
    for line in lines:
        line = line.split(seperator)
        if len(line) < count:
            continue
        for i in range(count):
            data_lists[i].append(line[i])

def extract_dropped_frames(result_dir):
    send_file = f'{result_dir}send.log'
    dropped_frames = []
    frame_sizes = []
    read_data_from_file(send_file, 3, [[], [], frame_sizes], ':')
    for i in range(1, len(frame_sizes)):
        frame_size = int(frame_sizes[i])
        if frame_size == 0:
            dropped_frames.append(i + 1)
    return dropped_frames

def generate_video(result_dir, width, height, dropped_frames):
    send_yuv = f'{result_dir}send.yuv'
    receive_raw_frames = f'{result_dir}receive_raw_frames/'
    print(receive_raw_frames)
    os.system("mkdir -p " + receive_raw_frames)
    receive_video = f'{result_dir}result.mkv'
    os.system(f'ffmpeg -i {receive_video} {receive_raw_frames}%d.png')
    
    receive_frame_cnt = len(os.listdir(receive_raw_frames))
    
    drop_number = 0
    
    f_output_yuv = open(f'{result_dir}receive_update.yuv', 'wb')
    for i in range(2, receive_frame_cnt + 1 + len(dropped_frames)):
        if i in dropped_frames:
            drop_number += 1
        rev_img_path = receive_raw_frames + str(i - drop_number) + ".png"
        rev_img = open(rev_img_path, 'rb').read()
        f_output_yuv.write(rev_img)
    f_output_yuv.close()
    
    os.system(f'ffmpeg -s {width}x{height} -i {result_dir}receive_update.yuv {result_dir}receive_update.mp4')
    
if __name__ == "__main__":
    result_dir = './'
    width = 1920
    height = 1080

    dropped_frames = extract_dropped_frames(result_dir)
    print(f'Dropped frames: {dropped_frames}')
    
    generate_video(result_dir, width, height, dropped_frames)
    
