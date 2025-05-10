vbv_ratios=(0.03 0.04 0.05 0.06 0.07 0.08 0.09 0.1 0.2 1.0)
trace_logs_dir="input/bitrate_config"
data="Lecture4_part"
repeat_time=2

for file in $(find ${trace_logs_dir} -maxdepth 1 -type f)
do
  for vbv_ratio in ${vbv_ratios[@]}
  do
    times=0
    while [ $times -lt $repeat_time ]
    do
      filename=$(basename -- "$file")
			filename="${filename%.*}"
      # filename=10to1
      vbv_ratio=1.0
      output_dir="result/${data}/${filename}/${vbv_ratio}_${times}/"
      echo $output_dir
      if [ ! -d "$output_dir" ]; then
          mkdir -p "$output_dir"
          echo "Directory '$output_dir' created."
      fi
      # /Users/menghua/Research/TestX264/build/test_libx264 $data $filename $vbv_ratio $output_dir
      python3 CalcDelayAndVmaf.py --data=${data} --bitrate=${filename} --vbvRatio=${vbv_ratio} --times=$times
      times=$((times+1))
      exit 0
    done
  done # vbv_ratio
  exit 0
done # bitrate file


#TODO:
# [v] 0. Read bitrate file and update codec
# [v] 1. output_diretory vbv_buffer_ratio 0.1 vs 0.10
# 2. Draw delay plot and frame size plot
# 3. Extract frames to calculate vmaf
# 4. Draw vmaf plot