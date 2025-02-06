#include "stdint.h"
#include "x264.h"
#include "x264_config.h"
#include <iostream>
#include <filesystem>
#include <string.h>
// Time Analysis
#include <chrono>
#include <vector>
#include <thread>
using namespace std;

#define QP 21 // Used when CQP
#define PRESET "superfast"
#define SMOOTH_BITRATE 0

const bool ENABLE_LOG = false;
const string FILE_PREFIX = "/Users/menghua/Research/TestX264/";

void InitEncodeParam(x264_param_t &param, int &initial_bitrate, int frame_rate, int width, int height, int default_vbv, bool enable_optimization) {
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
    // param.b_annexb = 1;  // for start code 0,0,0,1

    // Rate Control Method
    // // CQP
    // param.rc.i_rc_method = X264_RC_CQP;
    // param.rc.i_qp_constant = QP;

    // // CRF
    // param.rc.i_rc_method = X264_RC_CRF;
    // param.rc.f_rf_constant = 25;

    // ABR
    param.rc.i_rc_method = X264_RC_ABR;
    param.rc.i_bitrate = initial_bitrate;

    param.rc.i_vbv_max_bitrate = initial_bitrate + 1;

    if (enable_optimization) {
        // param.rc.i_qp_step = 50;
    }
    // param.rc.i_vbv_buffer_size = initial_bitrate / frame_rate * default_vbv; // kbit / 8 * 1000 = byte


    // param.rc.i_vbv_max_bitrate = initial_bitrate + default_vbv;
    param.rc.i_vbv_buffer_size = default_vbv; // kbit / 8 * 1000 = byte

    cout << "vbv size: " << param.rc.i_vbv_buffer_size << " i_bitrate: " << param.rc.i_bitrate << " max_bitrate: " << param.rc.i_vbv_max_bitrate << endl;

    param.i_log_level = X264_LOG_DEBUG;
    param.i_fps_den = 1;
    param.i_fps_num = frame_rate;

    // param_.b_vfr_input = 0;

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
        cout << config.start_frame_index << ',' << config.bitrate << endl;
        bitrate_config_vec.push_back(config);
    }
    if (ENABLE_LOG) {
        cout << "Read " << bitrate_config_vec.size() << " bitrate config" << endl;
        for (int i = 0; i < bitrate_config_vec.size(); i++) {
            cout << "start_frame_index:" << bitrate_config_vec[i].start_frame_index << " bitrate:" << bitrate_config_vec[i].bitrate << endl;
        }
    }
}

void UpdateBitrateConfig(x264_t *encoder, x264_param_t &param, int bitrate, int frame_rate, int vbv, int default_vbv, bool enable_optimization) {
    cout << "Reconfig to bitrate:" << bitrate << endl;
    param.rc.i_bitrate = bitrate;
    // if (param.rc.i_vbv_max_bitrate < bitrate || param.rc.i_vbv_max_bitrate < param.rc.i_vbv_buffer_size) {
    //     param.rc.i_vbv_max_bitrate = param.rc.i_vbv_buffer_size;
    // }
    param.rc.i_vbv_max_bitrate = bitrate;// + param.rc.i_vbv_buffer_size;; //  3000

    // if (enable_optimization) {
    //     param.rc.i_vbv_buffer_size = bitrate / frame_rate * vbv; // kbit / 8 * 1000 = byte  // 100
    // } else {
    //     param.rc.i_vbv_buffer_size = bitrate / frame_rate * default_vbv;
    // }

    cout << "vbv max bitrate: " << param.rc.i_vbv_max_bitrate << " vbv buffer: " << param.rc.i_vbv_buffer_size << endl;
    x264_encoder_reconfig(encoder, &param);
}

int WriteNALToFile(FILE *file_out, x264_nal_t *nal, int i_frame_size) {
    if (i_frame_size > 0) {
        if (!fwrite(nal->p_payload, i_frame_size, 1, file_out)) {
            cout << "fwrite failed" << endl;
            return -1;
        }
    } else if (i_frame_size < 0) {
        return -1;
    }
    return 0;
}

void EncodeAndGenerateStatistics(const string &video_name, const string &bitrate_config_filename, const string &output_filename, int initial_bitrate, int frame_rate, int width, int height,
                                 bool enable_optimization, bool drop_top_frame_when_network_change, bool drop_current_frame_when_buffer_full, int previous_drop_number, int default_vbv, int vbv) {
    x264_param_t param;
    x264_t *encoder;
    x264_picture_t pic;
    x264_picture_t pic_out;
    int i_frame = 0;
    int i_frame_size;
    x264_nal_t *nal;
    int i_nal;

    string bitrate_config_file =  FILE_PREFIX + "input/bitrate_config/" + bitrate_config_filename + ".txt";
    string input_video_file = FILE_PREFIX + "input/Lecture_720P_concat.yuv";
    string output_video_file = FILE_PREFIX + output_filename + ".mp4";

    InitEncodeParam(param, initial_bitrate, frame_rate, width, height, default_vbv, enable_optimization);

    // std::this_thread::sleep_for(std::chrono::seconds(2));

    FILE *input_yuv_file = fopen(input_video_file.c_str(), "rb");
    FILE *encoded_file_out = fopen(output_video_file.c_str(), "wb");
    FILE *bitrate_file = fopen(bitrate_config_file.c_str(), "rb");
    if (!input_yuv_file || !encoded_file_out || !bitrate_file) {
        cout << "fopen failed" << endl;
        return;
    }

    vector<BitrateConfig> bitrate_config_vec;
    ReadBitrateConfig(bitrate_file, bitrate_config_vec);

    if(x264_picture_alloc( &pic, param.i_csp, param.i_width, param.i_height) < 0 ) {
        cout << "x264_picture_alloc failed" << endl;
        return;
    }

    encoder = x264_encoder_open(&param);
    cout << "create encoder succeed!" << endl;
    if( !encoder ) return;

    int luma_size = param.i_width * param.i_height;
    int chroma_size = luma_size / 4;

    /* Encode frames */
    int current_bitrate = initial_bitrate;
    int bitrate_config_index = 0;
    for(;; i_frame++) {
        // Update bitrate limit if needed
        if (bitrate_config_index < bitrate_config_vec.size()) {
            int target_frame_index = bitrate_config_vec[bitrate_config_index].start_frame_index;
            if (i_frame == target_frame_index) {
                current_bitrate = bitrate_config_vec[bitrate_config_index].bitrate;
                UpdateBitrateConfig(encoder, param, current_bitrate, frame_rate, vbv, default_vbv, enable_optimization);
                bitrate_config_index++;
            }
        }

        /* Read input frame */
        if (fread(pic.img.plane[0], 1, luma_size, input_yuv_file) != (unsigned)luma_size) break;
        if (fread(pic.img.plane[1], 1, chroma_size, input_yuv_file) != (unsigned)chroma_size) break;
        if (fread(pic.img.plane[2], 1, chroma_size, input_yuv_file) != (unsigned)chroma_size) break;

        pic.i_pts = i_frame;

        i_frame_size = x264_encoder_encode(encoder, &nal, &i_nal, &pic, &pic_out);
        // cout << i_frame << ":" << i_frame_size << "  ";

        if (WriteNALToFile(encoded_file_out, nal, i_frame_size) < 0) {
            cout << "WriteNALToFile failed" << endl;
            return;
        }
    }
    // cout << endl;

    /* Flush delayed frames */
    while (x264_encoder_delayed_frames(encoder)) {
        if (WriteNALToFile(encoded_file_out, nal, i_frame_size) < 0) {
            cout << "WriteNALToFile failed" << endl;
            return;
        }
    }

    x264_encoder_close(encoder);
    x264_picture_clean(&pic);

    fclose(input_yuv_file);
    fclose(encoded_file_out);
    fclose(bitrate_file);
}

int main() {
    // Basic configurations
    int frame_rate = 30;
    int initial_bitrate = 3000; // 1M
    int default_vbv = 1000;
    int vbv = 1; // 10M; // When vbv is 1, the actual frame size should not exceed the target
    int previous_drop_number = 0;
    bool drop_current_frame_when_buffer_full = false;

    string input_bitrate_config_filenames[3] = {"3000-1500", "3000-300", "3000-50"};

    // // change bitrate config
    // string filenames[4] = {"default_no_drop", "default_drop", "opt_no_drop", "opt_drop"};
    // bool configurations[4][2] = {{false, false}, {false, true}, {true, false}, {true, true}};

    // EncodeAndGenerateStatistics("Gaming", "static", "test", initial_bitrate, frame_rate, 1920, 1080, false, false, drop_current_frame_when_buffer_full, previous_drop_number, default_vbv, vbv);
    //10000-1000
    EncodeAndGenerateStatistics("Gaming", "static", "test", initial_bitrate, frame_rate, 1280, 720, false, false, drop_current_frame_when_buffer_full, previous_drop_number, default_vbv, vbv);
    // EncodeAndGenerateStatistics("Gaming", "10000-1000", "test", initial_bitrate, frame_rate, 1280, 720, false, false, drop_current_frame_when_buffer_full, previous_drop_number, default_vbv, vbv);
    return 0;
}
