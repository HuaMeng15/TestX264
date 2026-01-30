#include "stdint.h"
#include "x264.h"
#include "x264_config.h"
#include <iostream>
#include <filesystem>
#include <string.h>
// Time Analysis
#include <chrono>
#include <vector>
#include <fstream>
#include <condition_variable>

using namespace std;

#define QP 21 // Used when CQP
#define PRESET "superfast"

const bool ENABLE_LOG = true;
const string FILE_PREFIX = "/Users/menghua/Research/TestX264/";
const string VIDEO_PREFIX = "/Users/menghua/Downloads/VideoSources/";
const string DIFFERENCE_DIR = "/Users/menghua/Research/TestX264/difference/";
const int SLICE_MAX_SIZE = 100;

void InitEncodeParam(x264_param_t &param, int initial_bitrate, int frame_rate, int width, int height) {
    x264_param_default_preset(&param, PRESET, "zerolatency");

    /* Configure non-default params */
    param.i_threads = 1;
    param.b_sliced_threads = 1;
    param.i_width = width;
    param.i_height = height;
    param.i_frame_total = 0;
    param.i_keyint_max = 1500;
    param.i_bitdepth = 8;
    param.i_csp = X264_CSP_I420;
    param.b_repeat_headers = 1;
    param.i_log_level = X264_LOG_DEBUG;
    param.i_log_level = X264_LOG_INFO;
    param.i_slice_max_size = SLICE_MAX_SIZE;
    // param.b_annexb = 1;  // for start code 0,0,0,1

    // Rate Control Method
    // ABR
    param.rc.i_rc_method = X264_RC_ABR;
    initial_bitrate = initial_bitrate;
    param.rc.i_bitrate = initial_bitrate;

    param.rc.i_vbv_max_bitrate = initial_bitrate;

    param.rc.i_vbv_buffer_size = initial_bitrate * 0.5; // kbit / 8 * 1000 = byte

    // param.rc.b_filler = 1;

    param.i_bframe = 0;
    param.b_open_gop = 0;
    // param.i_bframe_pyramid = 0;
    // param.i_bframe_adaptive = X264_B_ADAPT_TRELLIS;

    param.i_fps_den = 1;
    param.i_fps_num = frame_rate;

    param.b_vfr_input = 0;

    param.b_cabac = 1;  // 0 for CAVLC， 1 for higher complexity
}

struct BitrateConfig {
    int start_frame_index;
    int bitrate;
};

void ReadBitrateConfig(FILE *bitrate_file, vector<BitrateConfig> &bitrate_config_vec) {
    BitrateConfig config;
    while (fscanf(bitrate_file, "%d, %d", &config.start_frame_index,
                  &config.bitrate) != EOF) {
        // config.bitrate = config.bitrate / 2;
        bitrate_config_vec.push_back(config);
        if (config.start_frame_index == 0) {
            BitrateConfig config2 = config;
            config2.start_frame_index = 2; // avoid head I frame effect
            bitrate_config_vec.push_back(config2);
        }
    }
    if (ENABLE_LOG) {
        cout << "Read " << bitrate_config_vec.size() << " bitrate config" << endl;
        for (int i = 0; i < bitrate_config_vec.size(); i++) {
            cout << "start_frame_index:" << bitrate_config_vec[i].start_frame_index << " bitrate:" << bitrate_config_vec[i].bitrate << endl;
        }
    }
}

void UpdateBitrateConfig(x264_t *encoder, x264_param_t &param, int bitrate, double vbv_buffer_size) {
    bitrate = bitrate;
    cout << "Reconfig to bitrate:" << bitrate << " vbv_buffer_size:" << vbv_buffer_size << endl;
    param.rc.i_bitrate = bitrate;
    param.rc.i_vbv_max_bitrate = bitrate;// * 10;
    param.rc.i_vbv_buffer_size = bitrate * vbv_buffer_size;

    x264_encoder_reconfig(encoder, &param);
}

int WriteNALToFile(FILE *file_out, x264_nal_t *nal, int i_frame_size, int i_nal, int i_frame, int drop_frame = -1) {
    if (i_frame_size > 0) {
      fwrite(nal->p_payload, 1, i_frame_size, file_out);
    } else if (i_frame_size < 0) {
        return -1;
    }
    return 0;
}

const string GenerateVideoFilename(const string &video_name) {
    return VIDEO_PREFIX + video_name + ".yuv";
}

void EncodeAndGenerateStatistics(const string &video_name, const string &bitrate_config_filename, const string &output_dir, int initial_bitrate, int frame_rate, int width, int height) {
    x264_param_t param;
    x264_t *encoder;
    x264_picture_t pic;
    x264_picture_t pic_out;
    int i_frame = 0;
    int i_frame_size;
    x264_nal_t *nal;
    int i_nal;
    int current_bitrate = 0;

    string send_log_file = output_dir + "send.log";
    string bitrate_config_file =  FILE_PREFIX + "input/bitrate_config/" + bitrate_config_filename;
    string input_video_file = GenerateVideoFilename(video_name);
    cout << "input_video_file: " << input_video_file << endl;
    string output_video_file = output_dir + "result.mkv";

    if (!std::filesystem::is_directory(output_dir)) {
        cout << "Create directory: " <<  output_dir << endl;
        std::filesystem::create_directory(output_dir);
    }

    FILE *input_yuv_file = fopen(input_video_file.c_str(), "rb");
    FILE *encoded_file_out = fopen(output_video_file.c_str(), "wb");
    FILE *bitrate_file = fopen(bitrate_config_file.c_str(), "rb");
    std::ofstream send_file(send_log_file);
    std::ofstream frame_size_file(output_dir + "original_frame_size.log");
    if (!input_yuv_file || !encoded_file_out || !bitrate_file) {
        cout << "fopen failed input_yuv_file:" << !input_yuv_file << " encoded_file_out:" << !encoded_file_out << " bitrate_file: " << !bitrate_file << endl;
        return;
    }

    vector<BitrateConfig> bitrate_config_vec;
    ReadBitrateConfig(bitrate_file, bitrate_config_vec);

    current_bitrate = bitrate_config_vec[0].bitrate;
    int bitrate_config_index = 1;
    int drop_period_frames = 0;

    InitEncodeParam(param, current_bitrate, frame_rate, width, height);

    cout << "param i_bitrate: " << param.rc.i_bitrate << " max_bitrate: " << param.rc.i_vbv_max_bitrate << " vbv_buffer_size: " << param.rc.i_vbv_buffer_size << endl;

    if(x264_picture_alloc( &pic, param.i_csp, param.i_width, param.i_height) < 0 ) {
        cout << "x264_picture_alloc failed" << endl;
        return;
    }

    encoder = x264_encoder_open(&param);
    if( !encoder ) return;

    int luma_size = param.i_width * param.i_height;
    int chroma_size = luma_size / 4;

    int enable_drop = 0;

    /* Encode frames */
    for(;; i_frame++) {
        if (bitrate_config_index < bitrate_config_vec.size()) {
            if (i_frame == bitrate_config_vec[bitrate_config_index].start_frame_index) { /* target bitrate drop */
                current_bitrate = bitrate_config_vec[bitrate_config_index].bitrate;
                UpdateBitrateConfig(encoder, param, current_bitrate, 0.5);
                cout << "Update bitrate at frame" << i_frame << " Current bitrate: " << current_bitrate << " codec bitrate: " << param.rc.i_bitrate << " vbv_buffer_size: " << param.rc.i_vbv_buffer_size << endl;
                bitrate_config_index++;
            }
        }
        /* Read input frame */
        auto encode_start = chrono::high_resolution_clock::now();
        if (fread(pic.img.plane[0], 1, luma_size, input_yuv_file) != (unsigned)luma_size) break;
        if (fread(pic.img.plane[1], 1, chroma_size, input_yuv_file) != (unsigned)chroma_size) break;
        if (fread(pic.img.plane[2], 1, chroma_size, input_yuv_file) != (unsigned)chroma_size) break;

        pic.i_pts = i_frame;

        i_frame_size = x264_encoder_encode(encoder, &nal, &i_nal, &pic, &pic_out);

        if (WriteNALToFile(encoded_file_out, nal, i_frame_size, i_nal, i_frame) < 0) {
            cout << "WriteNALToFile failed" << endl;
            return;
        }
        cout << "Write frame: " << i_frame + 1 << " nal type: " << nal->i_type << " size: " << i_frame_size <<
        " size_kbps: " << i_frame_size * 8 * 30 / 1000 << " kbps" << " i_nal: " << i_nal << endl;

        auto encode_end = chrono::high_resolution_clock::now();
        auto encode_duration = chrono::duration_cast<chrono::milliseconds>(encode_end - encode_start);
        int encoded_duration = encode_duration.count();

        auto now = std::chrono::high_resolution_clock::now();
        // Convert to milliseconds since epoch
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();
        send_file << ms << " Encode frame:" << i_frame + 1 << " frame_size:" << i_frame_size << " :kbps: " << (i_frame_size * 240 / 1000) << std::endl;
        frame_size_file << i_frame + 1 << "," << i_frame_size << "," << (i_frame_size * 240 / 1000) << "," << i_nal << std::endl;
    }

    /* Flush delayed frames */
    while (x264_encoder_delayed_frames(encoder)) {
        if (WriteNALToFile(encoded_file_out, nal, i_frame_size, i_nal, i_frame) < 0) {
            cout << "WriteNALToFile failed" << endl;
            return;
        }
        cout << "Write delayed frame: " << i_frame + 1 << " nal type: " << nal->i_type << " size: " << i_frame_size << " kbps: " << (i_frame_size * 240 / 1000) << endl;
    }

    x264_encoder_close(encoder);
    x264_picture_clean(&pic);

    fclose(input_yuv_file);
    fclose(encoded_file_out);
    fclose(bitrate_file);
}

int main(int argc, char* argv[]) {
    if (argc < 3) {
        std::cerr << "Invalid arguments number:  " << argc << ", expected 3" << std::endl;
        return 1; // Return an error code
    }
    string video_name = argv[1];
    string bitrate_filename = argv[2];
    string output_dir = argv[3];
    cout << "video_name: " << video_name << " bitrate_filename: " << bitrate_filename << " output_dir: " << output_dir << endl;

    // Basic configurations
    int initial_bitrate = 10000;
    int width = 1920;
    int height = 1080;
    int frame_rate = 30;

    EncodeAndGenerateStatistics(video_name, bitrate_filename, output_dir, initial_bitrate, frame_rate, width, height);

    return 0;
}
