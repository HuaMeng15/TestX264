#!/bin/bash
vbv_ratios=(0.03 0.04 0.05 0.06 0.07 0.08 0.09 0.1 0.2 0.5 0.7 1.0)
vbv_ratios=(0.04 0.06 0.08 0.1 0.3 0.5 0.7 1.0)
vbv_ratios=(0.3 0.04)
vbv_ratios=(0.04 0.06 0.08 0.1 0.2 0.3)
vbv_ratios=(0.3)
reduce_numbers=(16)
dropped_vbv_ratios=(0.04)
# vbv_ratios=(0.03)
trace_logs_dir="input/bitrate_config"
datas=('Game_gray' 'Lecture1080p' 'Game_minecraft' 'Game_scene_change' 'Game_screen' 'Game_shoot' 'Game_shoot_static' 'ReadySteadyGo' 'static')
datas=('Game_gray_part' 'ReadySteadyGo' 'scene_change' 'Lecture1080p')
datas=('ReadySteadyGo8s')
repeat_time=1
# traces=('5to1' '5to2' '10to5' '20to2' '10to2' '2to1' )
traces=('static_1mbps' 'static_2mbps' 'static_5mbps' 'static_10mbps' 'static_20mbps')
traces=('5to1' '2to1' '30to1')
traces=('10to5' '10to2' '10to1' '30to3')
suffixs=('_' '_adaptive_')
suffixs=('_')
speeds=(1 2 4 8)
qp_steps=(1 2 4 8 10 20)
qp_steps=(4)

result_dir='result/ReadySteadyGo/10to1'

# for file in $(find ${trace_logs_dir} -maxdepth 1 -type f)
# for suffix in ${suffixs[@]}
for data in ${datas[@]}
# for file in $(find ${result_dir} -maxdepth 1 -type d)
do
  # for speed in ${speeds[@]}
  # for qp_step in ${qp_steps[@]}
  for reduce_number in ${reduce_numbers[@]}
  do
    for trace in ${traces[@]}
    do
      for vbv_ratio in ${vbv_ratios[@]}
      # for dropped_vbv_ratio in ${dropped_vbv_ratios[@]}
      do
        data='ReadySteadyGo'
        # data='Lecture1080p'
        # trace='5to1'
        trace='30to3'
        # reduce_number=10
        dropped_vbv_ratio=0.04
        # vbv_ratio=0.3
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
        output_dir="result/${data_file}/${trace_filename}/${vbv_ratio}_drop_${reduce_number}_interval_4/"
        # output_dir="result/${data_file}/${trace_filename}/${vbv_ratio}_adaptive/"
        # output_dir="result/${data_file}/${trace_filename}/${vbv_ratio}/"
        output_dir="result/${data_file}/${trace_filename}/x264_${vbv_ratio}/"
        echo $output_dir
        if [ ! -d "$output_dir" ]; then
            mkdir -p "$output_dir"
            echo "Directory '$output_dir' created."
        fi
        # x264
        # build/test_libx264 $data_file $trace_filename $vbv_ratio $output_dir 30 $qp_step $dropped_vbv_ratio $reduce_number
        # exit 0
        # cp ${qp_file} "${output_dir}/qp.log"
        python3 CalcDelayAndVmaf.py --data=${data_file} --bitrate=${trace_filename} --vbvRatio=${vbv_ratio} --output_dir=${output_dir}

        # x265
        # build/test_libx265 $data_file $trace_filename $vbv_ratio $output_dir 30 $qp_step $dropped_vbv_ratio $reduce_number
        # # cp ${qp_file} "${output_dir}/qp.log"
        # python3 CalcDelayAndVmaf.py --data=${data_file} --bitrate=${trace_filename} --vbvRatio=${vbv_ratio} --output_dir=${output_dir}
        exit 0
      done # vbv_ratio
      # exit 0
    done # bitrate file
    # exit 0
  done # speed
  # exit 0
done # data
