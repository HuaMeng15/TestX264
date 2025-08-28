#!/bin/bash
vbv_ratios=(0.3)
reduce_numbers=(14)
dropped_vbv_ratios=(0.04)
# vbv_ratios=(0.03)
trace_logs_dir="input/bitrate_config"
datas=('ReadySteadyGo')
repeat_time=1
traces=('static_1mbps' 'static_2mbps' 'static_5mbps' 'static_10mbps' 'static_20mbps')
# traces=('10to1' '5to1' '2to1' '10to5' '10to2')
traces=('10to1')
suffixs=('_')
speeds=(1 2 4 8)
qp_steps=(4)

for data in ${datas[@]}
do
  for reduce_number in ${reduce_numbers[@]}
  do
    for trace in ${traces[@]}
    do
      for vbv_ratio in ${vbv_ratios[@]}
      # for dropped_vbv_ratio in ${dropped_vbv_ratios[@]}
      do
        # trace='5to1'
        # trace='10to1'
        # reduce_number=10
        dropped_vbv_ratio=0.04
        # vbv_ratio=0.04
        speed=1
        qp_step=4
        trace_filename=$(basename -- "$trace")
        trace_filename="${trace_filename%.*}"

        if [ "$speed" -eq 1 ]; then
            data_file="${data}"
        else
            data_file="${data}_${speed}x"
        fi

        qp_file='temp.log'
        if [ -f "$qp_file" ]; then
            rm "$qp_file"
            echo "File '$qp_file' removed."
        fi

        # output_dir="${file}/"
        output_dir="result/${data_file}/${trace_filename}/${vbv_ratio}_drop_${reduce_number}_interval_3/"
        # output_dir="result/${data_file}/${trace_filename}/${vbv_ratio}_adaptive/"
        output_dir="result/${data_file}/${trace_filename}/${vbv_ratio}/"
        # output_dir="result/${data_file}/${trace_filename}/0.3+0.06/"
        echo $output_dir
        if [ ! -d "$output_dir" ]; then
            mkdir -p "$output_dir"
            echo "Directory '$output_dir' created."
        fi
        build/test_libx264 $data_file $trace_filename $vbv_ratio $output_dir 30 $qp_step $dropped_vbv_ratio $reduce_number
        cp ${qp_file} "${output_dir}/qp.log"
        python3 CalcDelayAndVmaf.py --data=${data_file} --bitrate=${trace_filename} --vbvRatio=${vbv_ratio} --output_dir=${output_dir}
        exit 0
      done # vbv_ratio
      # exit 0
    done # bitrate file
    # exit 0
  done # speed
  # exit 0
done # data