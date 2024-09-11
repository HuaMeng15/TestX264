
#include "stdint.h"
#include "x264.h"
#include "x264_config.h"
#include <iostream>
//memcpy
#include <string.h>
// Time Analysis
#include <chrono>
#include <vector>
using namespace std;

#define QP 21 // Used when CQP
#define PRESET "superfast"
#define VBV 1   // When VBV is 1, the actual frame size should not exceed the target
#define INITIAL_BITRATE 3000
#define FRAME_RATE 30
#define MAX_BITRATE_BUFFER 50
#define SMOOTH_BITRATE 1

const string FILE_PREFIX = "/Users/menghua/Research/TestX264/";
const string BITRATE_CONFIG_FILE =  FILE_PREFIX + "input/bitrate_config.txt";
const string BITRATE_CONFIG_OUT_FILE = FILE_PREFIX + "input/bitrate_config_out.txt";
const string INPUT_VIDEO_FILE = FILE_PREFIX + "input/1280x720.yuv";
const string OUTPUT_VIDEO_FILE = FILE_PREFIX + "result/with_bitrate_buffer_with_smooth.mkv";
const string STATISTICS_RESULT_FILE = FILE_PREFIX + "result/statistics_with_bitrate_buffer_with_smooth.csv";

void InitEncodeParam(x264_param_t &param, int &width, int &height, int &initial_bitrate) {
    x264_param_default_preset(&param, PRESET, "zerolatency");

    /* Configure non-default params */
    param.i_threads = 2;
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
    param.rc.i_qp_step = 50;

    param.rc.i_vbv_max_bitrate = initial_bitrate + MAX_BITRATE_BUFFER;
    param.rc.i_vbv_buffer_size = initial_bitrate / FRAME_RATE * VBV; // kbit / 8 * 1000 = byte  // 100
    // param.rc.b_filler = 1;

    // param.i_bframe = 0;
    // param.b_open_gop = 0;
    // param.i_bframe_pyramid = 0;
    // param.i_bframe_adaptive = X264_B_ADAPT_TRELLIS;

    // param.i_log_level = X264_LOG_DEBUG;
    param.i_fps_den = 1;
    param.i_fps_num = FRAME_RATE;

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
        bitrate_config_vec.push_back(config);
    }
    cout << "Read " << bitrate_config_vec.size() << " bitrate config" << endl;
    for (int i = 0; i < bitrate_config_vec.size(); i++) {
        cout << "start_frame_index:" << bitrate_config_vec[i].start_frame_index << " bitrate:" << bitrate_config_vec[i].bitrate << endl;
    }
}

void UpdateBitrateConfig(x264_t *encoder, x264_param_t &param, int bitrate) {
    cout << "Reconfig to bitrate:" << bitrate << endl;
    param.rc.i_bitrate = bitrate;
    param.rc.i_vbv_max_bitrate = bitrate + MAX_BITRATE_BUFFER; //  3000
    param.rc.i_vbv_buffer_size = bitrate / FRAME_RATE * VBV; // kbit / 8 * 1000 = byte  // 100

    // param_.analyse.i_trellis = 1;
    // param_.analyse.inter = X264_ANALYSE_I4x4 | X264_ANALYSE_I8x8
    //             | X264_ANALYSE_PSUB16x16 | X264_ANALYSE_BSUB16x16;
    // param_.analyse.i_subpel_refine = 4;           
    // param_.analyse.i_me_method = X264_ME_HEX;  
    // param_.i_frame_reference = 2;
    x264_encoder_reconfig(encoder, &param);
}

void ModifyBitrateConfig(vector<BitrateConfig> &bitrate_config_vec, FILE *bitrate_file_out) {
    int previous_frame_index = -1, previous_bitrate = -1;
    vector<BitrateConfig> modifed_bitrate_config_vec;
    for (auto& bitrate_config : bitrate_config_vec) {
        if (previous_frame_index == -1) {
            previous_frame_index = bitrate_config.start_frame_index;
            previous_bitrate = bitrate_config.bitrate;
        } else {
            int bitrate_diff = bitrate_config.bitrate - previous_bitrate;
            int frame_count = bitrate_config.start_frame_index - previous_frame_index;
            int bitrate_step = bitrate_diff / frame_count;
            for (int i = 0; i < frame_count; i++) {
                fprintf(bitrate_file_out, "%d, %d\n", previous_frame_index + i, previous_bitrate + i * bitrate_step);
                BitrateConfig config;
                config.start_frame_index = previous_frame_index + i;
                config.bitrate = previous_bitrate + i * bitrate_step;
                modifed_bitrate_config_vec.push_back(config);
            }
            previous_frame_index = bitrate_config.start_frame_index;
            previous_bitrate = bitrate_config.bitrate;
        }
    }
    bitrate_config_vec = modifed_bitrate_config_vec;
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

struct Statistics {
    int current_bitrate;
    int frame_size;
    int duration;
};

void OutputStatistics(vector<Statistics> &statistics_result) {
    // write the frame size to file
    FILE *statistics_file = fopen(STATISTICS_RESULT_FILE.c_str(), "w");
    // fprintf(statistics_file, "current_bitrate,frame_size,duration\n");
    for (int i = 0; i < statistics_result.size(); i++) {
        fprintf(statistics_file, "%d,%d,%d\n", statistics_result[i].current_bitrate,
                statistics_result[i].frame_size, statistics_result[i].duration);
    }
    fclose(statistics_file);
}

int main() {
    x264_param_t param;
    x264_t *encoder;
    x264_picture_t pic;
    x264_picture_t pic_out;
    int i_frame = 0;
    int i_frame_size;
    x264_nal_t *nal;
    int i_nal;
    int initial_bitrate = INITIAL_BITRATE;

    int width = 1280;
    int height = 720;

    InitEncodeParam(param, width, height, initial_bitrate);

    FILE *input_yuv_file = fopen(INPUT_VIDEO_FILE.c_str(), "rb");
    FILE *encoded_file_out = fopen(OUTPUT_VIDEO_FILE.c_str(), "wb");
    FILE *bitrate_file = fopen(BITRATE_CONFIG_FILE.c_str(), "rb");
    FILE *bitrate_file_out = nullptr;
    if (SMOOTH_BITRATE) {
        bitrate_file_out = fopen(BITRATE_CONFIG_OUT_FILE.c_str(), "w");
    }
    if (!input_yuv_file || !encoded_file_out || !bitrate_file || (SMOOTH_BITRATE && !bitrate_file_out)) {
        cout << "fopen failed" << endl;
        return -1;
    }

    vector<BitrateConfig> bitrate_config_vec;
    ReadBitrateConfig(bitrate_file, bitrate_config_vec);
    if (bitrate_file_out) {
        ModifyBitrateConfig(bitrate_config_vec, bitrate_file_out);
        ReadBitrateConfig(bitrate_file_out, bitrate_config_vec);
    }

    if(x264_picture_alloc( &pic, param.i_csp, param.i_width, param.i_height) < 0 ) {
        cout << "x264_picture_alloc failed" << endl;
        return -1;
    }

    encoder = x264_encoder_open(&param);
    if( !encoder ) return -1;

    int luma_size = width * height;
    int chroma_size = luma_size / 4;

    /* Encode frames */
    int current_bitrate = initial_bitrate;
    int bitrate_config_index = 0;
    vector<Statistics> statistics_result;
    for(;; i_frame++) {
        // Update bitrate limit if needed
        if (bitrate_config_index < bitrate_config_vec.size() &&
            i_frame == bitrate_config_vec[bitrate_config_index].start_frame_index) {
            current_bitrate = bitrate_config_vec[bitrate_config_index].bitrate;
            UpdateBitrateConfig(encoder, param, current_bitrate);
            bitrate_config_index++;
        }

        /* Read input frame */
        if (fread(pic.img.plane[0], 1, luma_size, input_yuv_file) != (unsigned)luma_size) break;
        if (fread(pic.img.plane[1], 1, chroma_size, input_yuv_file) != (unsigned)chroma_size) break;
        if (fread(pic.img.plane[2], 1, chroma_size, input_yuv_file) != (unsigned)chroma_size) break;

        pic.i_pts = i_frame;

        // time analysis
        auto encode_start = chrono::high_resolution_clock::now();
        i_frame_size = x264_encoder_encode(encoder, &nal, &i_nal, &pic, &pic_out);
        auto encode_end = chrono::high_resolution_clock::now();

        auto duration = chrono::duration_cast<chrono::milliseconds>(encode_end - encode_start);

        Statistics statistics;//{current_bitrate, i_frame_size, duration.count()};
        statistics.current_bitrate = current_bitrate * 1000 / (8 * FRAME_RATE); // kbit to byte per frame
        statistics.frame_size = i_frame_size;
        statistics.duration = duration.count();
        statistics_result.push_back(statistics);
        // cout << "real frame size:" << i_frame_size << endl;

        if (WriteNALToFile(encoded_file_out, nal, i_frame_size) < 0) {
            cout << "WriteNALToFile failed" << endl;
            return -1;
        }
    }

    /* Flush delayed frames */
    while (x264_encoder_delayed_frames(encoder)) {
        if (WriteNALToFile(encoded_file_out, nal, i_frame_size) < 0) {
            cout << "WriteNALToFile failed" << endl;
            return -1;
        }
    }

    x264_encoder_close(encoder);
    x264_picture_clean(&pic);

    OutputStatistics(statistics_result);

    fclose(input_yuv_file);
    fclose(encoded_file_out);
    fclose(bitrate_file);

    return 0;
}