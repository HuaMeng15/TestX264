#!/bin/bash
vbv_ratios=(0.03 0.04 0.05 0.06 0.07 0.08 0.09 0.1 0.2 0.5 0.7 1.0)
vbv_ratios=(0.1 0.3 0.5 0.7 1.0)
trace_logs_dir="input/bitrate_config"
data="Lecture_1080p"
repeat_time=5
traces=('5to1' '5to2' '10to5' '20to2' '10to2' '2to1' )
suffixs=('_' '_adaptive_')
suffixs=('_')

# for file in $(find ${trace_logs_dir} -maxdepth 1 -type f)
for suffix in ${suffixs[@]}
do
  # file='static_10mbps'
  for vbv_ratio in ${vbv_ratios[@]}
  do
    times=2
    while [ $times -lt $repeat_time ]
    do
      filename=$(basename -- "$file")
			filename="${filename%.*}"
      filename='static_10mbps'
      vbv_ratio=0.3
      # suffix="_adaptive_"
      # output_dir="result/${data}/${filename}/${vbv_ratio}_${times}/"
      output_dir="result/${data}/${filename}/${vbv_ratio}${suffix}${times}/"
      output_dir="result/${data}/${filename}/test2/"
      echo $output_dir
      if [ ! -d "$output_dir" ]; then
          mkdir -p "$output_dir"
          echo "Directory '$output_dir' created."
      fi
      build/test_libx264 $data $filename $vbv_ratio $output_dir $times $suffix
      python3 CalcDelayAndVmaf.py --data=${data} --bitrate=${filename} --vbvRatio=${vbv_ratio} --times=$times --output_dir=${output_dir}
      times=$((times+1))
      exit 0
    done
  done # vbv_ratio
  # exit 0
done # bitrate file


#TODO:
# [v] 0. Read bitrate file and update codec
# [v] 1. output_diretory vbv_buffer_ratio 0.1 vs 0.10
# 2. Draw delay plot and frame size plot
# [v] 3. Extract frames to calculate vmaf
# 4. Draw vmaf plot