#include <iostream>
using namespace std;

int main() {
  //read the bitrate config
  FILE *bitrate_file = fopen("/Users/menghua/Research/TestX264/input/bitrate_config.txt", "rb");
  // write the modified bitrate to file
  FILE *bitrate_file_out = fopen("/Users/menghua/Research/TestX264/bitrate_config_out2.txt", "w");
  if (!bitrate_file_out || !bitrate_file) {
    std::cout << "fopen failed" << std::endl;
    return -1;
  }

  int frame_index = -1, bitrate = -1, next_frame_index = -1, next_bitrate = -1;
  while (fscanf(bitrate_file, "%d, %d", &next_frame_index, &next_bitrate) != EOF) {
        if (frame_index == -1) {
          frame_index = next_frame_index;
          bitrate = next_bitrate;
        } else {
          int bitrate_diff = next_bitrate - bitrate;
          int frame_count = next_frame_index - frame_index;
          int bitrate_step = bitrate_diff / frame_count;
          for (int i = 0; i < frame_count; i++) {
            fprintf(bitrate_file_out, "%d, %d\n", frame_index + i, bitrate + i * bitrate_step);
          }
        }
    }
}