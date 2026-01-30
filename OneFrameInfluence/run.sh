#!/bin/bash
trace_logs_dir="input/bitrate_config"
datas=('ReadySteadyGo' 'Lecture')
traces=('static_30mbps' 'static_3mbps')

for data in ${datas[@]}
do
  for trace in ${traces[@]}
  do
    trace_filename=$(basename -- "$trace")
    trace_filename="${trace_filename%.*}"
    output_dir="result/${data}/${trace_filename}/"
    echo $output_dir
    if [ ! -d "$output_dir" ]; then
        mkdir -p "$output_dir"
        echo "Directory '$output_dir' created."
    fi
    # x264
    # build/one_frame_influence $data_file $trace_filename $output_dir
    # exit 0
    # python3 CalcDelayAndVmaf.py --data=${data_file} --bitrate=${trace_filename} --vbvRatio=${vbv_ratio} --output_dir=${output_dir}
  done # bitrate file
done # data
