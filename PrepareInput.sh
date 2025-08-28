#!/bin/bash
video_dir="/home/eceuser/video_resources/"
input_dir="/home/eceuser/menghua/Research/TestX264/input/"

width=1920
height=1080

for file in $(find ${video_dir} -type f)
do
  suffix="${file##*.}"
  if [ "$suffix" != "yuv" ] || [[ "$file" == *"720"* ]]; then
    continue
  fi
  filename=$(basename -- "$file")
  filename="${filename%.*}"
  echo "Processing file: $filename $suffix"
  # mkdir -p "${input_dir}${filename}_raw_frames/"
  # ffmpeg -s "${width}x${height}" -i "${file}" "${input_dir}${filename}_raw_frames/%d.png"
done # video file