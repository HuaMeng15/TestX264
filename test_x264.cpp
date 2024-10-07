#include "stdint.h"
#include "x264.h"
#include "x264_config.h"
#include <iostream>
#include <filesystem>
#include <string.h>
// Time Analysis
#include <chrono>
#include <vector>
using namespace std;

#define QP 21 // Used when CQP
#define PRESET "superfast"
#define SMOOTH_BITRATE 0

const bool ENABLE_LOG = true;
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

    param.rc.i_vbv_max_bitrate = initial_bitrate;

    if (enable_optimization) {
        // param.rc.i_qp_step = 50;
    }
    param.rc.i_vbv_buffer_size = initial_bitrate / frame_rate * default_vbv; // kbit / 8 * 1000 = byte

    // param.rc.b_filler = 1;

    // param.i_bframe = 0;
    // param.b_open_gop = 0;
    // param.i_bframe_pyramid = 0;
    // param.i_bframe_adaptive = X264_B_ADAPT_TRELLIS;

    // param.i_log_level = X264_LOG_DEBUG;
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
    param.rc.i_vbv_max_bitrate = bitrate; //  3000

    if (enable_optimization) {
        param.rc.i_vbv_buffer_size = bitrate / frame_rate * vbv; // kbit / 8 * 1000 = byte  // 100
    } else {
        param.rc.i_vbv_buffer_size = bitrate / frame_rate * default_vbv;
    }

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

struct NetworkBufferFrame {
    int frame_index;
    int frame_size;
    int buffer_size;
};

struct FrameSendReceiveTimeRecord {
    int frame_index;
    int frame_size;
    double send_time_point;
    double receive_time_point;
    double display_time_point;
    double receive_delay;
    double display_delay;
    int send_frame_index_when_display;
};

void UpdateFrameReceiveTimeRecord(vector<FrameSendReceiveTimeRecord> &frame_send_receive_time_records,
                                  int current_frame_index, double current_time_point, double &display_time_point,
                                  int send_frame_index_when_display) {
    for (int i = 0; i < frame_send_receive_time_records.size(); i++) {
        if (frame_send_receive_time_records[i].frame_index == current_frame_index) {
            frame_send_receive_time_records[i].receive_time_point = current_time_point;
            frame_send_receive_time_records[i].receive_delay = current_time_point - frame_send_receive_time_records[i].send_time_point;
            display_time_point = std::max(display_time_point, current_time_point);
            frame_send_receive_time_records[i].display_time_point = display_time_point;
            frame_send_receive_time_records[i].display_delay = display_time_point - frame_send_receive_time_records[i].send_time_point;
            frame_send_receive_time_records[i].send_frame_index_when_display = send_frame_index_when_display;

            if (ENABLE_LOG) {
                cout << "***** Receive Frame index: " << frame_send_receive_time_records[i].frame_index << " Time point: " << current_time_point << " Delay: " << frame_send_receive_time_records[i].receive_delay << " Send point: " <<  frame_send_receive_time_records[i].send_time_point << endl;
                cout << "***** Display Frame index: " << frame_send_receive_time_records[i].frame_index << " Time point: " << display_time_point << " Delay: " << frame_send_receive_time_records[i].display_delay << " Send point: " <<  frame_send_receive_time_records[i].send_time_point << endl;
                cout << "***** Send Frame index when display: " << frame_send_receive_time_records[i].send_frame_index_when_display << endl;
            }

            break;
        }
    }
}

double CalcTransmitTimeBySize(double size, double bitrate) {
    return size * 1000 / bitrate;
}

void UpdateBufferFrames(vector<NetworkBufferFrame> &network_buffer_frames, vector<FrameSendReceiveTimeRecord> &frame_send_receive_time_records,
                        int current_frame_index, int current_frame_size,
                        int &network_remain_buffer_size, int network_buffer_size, int transmit_size, vector<int> &dropped_frame_indexs,
                        double current_time_point, int current_bitrate, double &display_time_point, int &send_frame_index_when_display,
                        int frame_rate, bool drop_current_frame_when_buffer_full) {
    if (ENABLE_LOG) {
        cout << "---------------------------Transmit size: " << transmit_size << "---------------------------------" << endl;
    }
    // transmit one frame
    network_remain_buffer_size = min(network_remain_buffer_size + transmit_size, network_buffer_size);
    double finish_send_time_point = current_time_point;
    while (transmit_size > 0 && !network_buffer_frames.empty()) {
        NetworkBufferFrame &frame = network_buffer_frames.front();
        if (frame.buffer_size <= transmit_size) {
            transmit_size -= frame.buffer_size;
            if (ENABLE_LOG) {
                cout << "Finish Transmit frame: " << frame.frame_index << " overall size: " << frame.frame_size << " frame.buffer_size: " << frame.buffer_size << " finished. transmit_size: " << transmit_size << endl;
            }
            double send_cost_time = CalcTransmitTimeBySize(frame.buffer_size, current_bitrate);
            send_frame_index_when_display = std::max(send_frame_index_when_display, current_frame_index);
            UpdateFrameReceiveTimeRecord(frame_send_receive_time_records, frame.frame_index, finish_send_time_point + send_cost_time, display_time_point, send_frame_index_when_display);
            send_frame_index_when_display++;
            display_time_point += 1000.0 / frame_rate;
            finish_send_time_point += send_cost_time;
            network_buffer_frames.erase(network_buffer_frames.begin());
        } else {
            frame.buffer_size -= transmit_size;
            transmit_size = 0;
            if (ENABLE_LOG) {
                cout << "Transmit part of the frame: " << frame.frame_index << " overall size: " << frame.frame_size << " frame.buffer_size: " << frame.buffer_size << " transmit_size: " << transmit_size << endl;
            }
        }
    }

    // try to insert the current frame into the buffer
    if (current_frame_size < 0) { return; }
    if (current_frame_size > network_remain_buffer_size) {
        if (drop_current_frame_when_buffer_full) { // drop current frame.
            dropped_frame_indexs.push_back(current_frame_index);
            cout << "Drop frame: " << current_frame_index << " overall size: " << current_frame_size << " remain_size: " << network_remain_buffer_size << endl;
            return;
        }
        while (current_frame_size > network_remain_buffer_size) {
            NetworkBufferFrame &frame = network_buffer_frames.front();
            network_remain_buffer_size += frame.buffer_size;
            network_buffer_frames.erase(network_buffer_frames.begin());
            dropped_frame_indexs.push_back(frame.frame_index);
            cout << "Drop frame: " << frame.frame_index << " overall size: " << frame.frame_size <<  " frame.buffer_size: " << frame.buffer_size << " remain_size: " << network_remain_buffer_size << endl;
        }
    }
    network_remain_buffer_size -= current_frame_size;
    NetworkBufferFrame frame;
    frame.frame_index = current_frame_index;
    frame.frame_size = current_frame_size;
    frame.buffer_size = current_frame_size;
    network_buffer_frames.push_back(frame);
    FrameSendReceiveTimeRecord record;
    record.frame_index = current_frame_index;
    record.frame_size = current_frame_size;
    record.send_time_point = current_time_point;
    frame_send_receive_time_records.push_back(record);
    if (ENABLE_LOG) {
        cout << "Insert frame: " << current_frame_index << " overall size: " << current_frame_size << " network_remain_buffer_size: " << network_remain_buffer_size << endl;
        cout << "Send Frame index: " << current_frame_index << " Time point: " << current_time_point << endl;
    }
}

struct Statistics {
    int current_bitrate;
    int frame_size;
    int duration;
};

void OutputFrameSizeStatistics(vector<Statistics> &statistics_result, const string &frame_size_statistics_file) {
    // write the frame size to file
    FILE *statistics_file = fopen(frame_size_statistics_file.c_str(), "w");
    fprintf(statistics_file, "current_bitrate,frame_size,duration\n");
    for (int i = 0; i < statistics_result.size(); i++) {
        fprintf(statistics_file, "%d,%d,%d\n", statistics_result[i].current_bitrate,
                statistics_result[i].frame_size, statistics_result[i].duration);
    }
    fclose(statistics_file);
}

void OutputRenderFrameIndex(vector<int> &dropped_frame_indexs, int frame_number, const string &render_frame_index_file) {
    FILE *frame_index_file = fopen(render_frame_index_file.c_str(), "w");
    int last_rendered_frame_index = 0;
    int drop_vector_index = 0;
    for (int i = 0; i < frame_number; i++) {
        int render_frame_index = i;
        if (drop_vector_index < dropped_frame_indexs.size() &&
            i == dropped_frame_indexs[drop_vector_index]) {
            drop_vector_index++;
            render_frame_index = last_rendered_frame_index;
        }
        last_rendered_frame_index = render_frame_index;
        fprintf(frame_index_file, "%d, %d\n", i, render_frame_index);
    }
    fclose(frame_index_file);
}

void OutputDelayStatistics(vector<FrameSendReceiveTimeRecord> &frame_send_receive_time_records, const string &delay_statistics_file) {
    FILE *delay_time_file = fopen(delay_statistics_file.c_str(), "w");
    fprintf(delay_time_file, "frame_index, frame_size, send_frame_index_when_display, send_time_point, receive_time_point, display_time_point, receive_delay, display_delay\n");
    for (int i = 0; i < frame_send_receive_time_records.size() - 1; i++) {
        auto record = frame_send_receive_time_records[i];
        fprintf(delay_time_file, "%d, %d, %d, %f, %f, %f, %f, %f\n", record.frame_index, record.frame_size, record.send_frame_index_when_display, record.send_time_point, record.receive_time_point, record.display_time_point, record.receive_delay, record.display_delay);
    }
    fclose(delay_time_file);
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

    string result_directory_name = video_name + "_" + bitrate_config_filename + "/";
    string result_filename = result_directory_name + output_filename;
    string bitrate_config_file =  FILE_PREFIX + "input/bitrate_config/" + bitrate_config_filename + ".txt";
    string bitrate_config_out_file = FILE_PREFIX + "input/bitrate_config_out.txt";
    string input_video_file = FILE_PREFIX + "input/" + video_name + "_" + std::to_string(width) + "x" + std::to_string(height) + ".yuv";
    string output_video_file = FILE_PREFIX + "result/" + result_filename + ".mkv";
    string frame_size_statistics_file = FILE_PREFIX + "result/" + result_filename + ".csv";
    string render_frame_index_file = FILE_PREFIX + "/result/" + result_filename + "_render_frame.txt";
    string delay_statistics_file = FILE_PREFIX + "/result/" + result_filename + "_delay_statistics.csv";

    InitEncodeParam(param, initial_bitrate, frame_rate, width, height, default_vbv, enable_optimization);

    if (!std::filesystem::is_directory(FILE_PREFIX + "result/" + result_directory_name)) {
        cout << "Create directory: " <<  FILE_PREFIX + "result/" + result_directory_name << endl;
        std::filesystem::create_directory(FILE_PREFIX + "result/" + result_directory_name);
    }

    FILE *input_yuv_file = fopen(input_video_file.c_str(), "rb");
    FILE *encoded_file_out = fopen(output_video_file.c_str(), "wb");
    FILE *bitrate_file = fopen(bitrate_config_file.c_str(), "rb");
    FILE *bitrate_file_out = nullptr;
    if (SMOOTH_BITRATE) {
        bitrate_file_out = fopen(bitrate_config_out_file.c_str(), "w");
    }
    if (!input_yuv_file || !encoded_file_out || !bitrate_file || (SMOOTH_BITRATE && !bitrate_file_out)) {
        cout << "fopen failed" << endl;
        return;
    }

    vector<BitrateConfig> bitrate_config_vec;
    ReadBitrateConfig(bitrate_file, bitrate_config_vec);
    if (bitrate_file_out) {
        ModifyBitrateConfig(bitrate_config_vec, bitrate_file_out);
        ReadBitrateConfig(bitrate_file_out, bitrate_config_vec);
    }

    if(x264_picture_alloc( &pic, param.i_csp, param.i_width, param.i_height) < 0 ) {
        cout << "x264_picture_alloc failed" << endl;
        return;
    }

    encoder = x264_encoder_open(&param);
    if( !encoder ) return;

    int luma_size = param.i_width * param.i_height;
    int chroma_size = luma_size / 4;

    /* Encode frames */
    int current_bitrate = initial_bitrate;
    // TODO: start from 1, ignore the initial frame because we have set in the code to 3000
    int bitrate_config_index = 1;
    int encode_duration = 0;
    vector<Statistics> statistics_result;
    int change_index = -1;
    int network_buffer_size = current_bitrate / 5; // kbit, max 200ms delay
    int network_remain_buffer_size = network_buffer_size; // kbit
    double each_frame_time = 1000.0 / frame_rate; // ms
    double current_time_point = 0;
    double display_time_point = 0;
    int send_frame_index_when_display = 0;
    vector<NetworkBufferFrame> network_buffer_frames;
    vector<FrameSendReceiveTimeRecord> frame_send_receive_time_records;
    vector<int> dropped_frame_indexs;
    for(;; i_frame++) {
        // if (i_frame == 2) {
        //     param.rc.i_vbv_buffer_size = current_bitrate / frame_rate * 1;
        //     x264_encoder_reconfig(encoder, &param);
        // }
        // Update bitrate limit if needed
        if (bitrate_config_index < bitrate_config_vec.size()) {
            int target_frame_index = bitrate_config_vec[bitrate_config_index].start_frame_index;
            if (i_frame == target_frame_index) {
                current_bitrate = bitrate_config_vec[bitrate_config_index].bitrate;
                UpdateBitrateConfig(encoder, param, current_bitrate, frame_rate, vbv, default_vbv, enable_optimization);
                bitrate_config_index++;

                // Update network buffer size
                int current_occupy_buffer_size =  network_buffer_size - network_remain_buffer_size;
                network_buffer_size = current_bitrate / 5;
                if (ENABLE_LOG) {
                    cout << "Update network_buffer_size to " << network_buffer_size << " current_occupy_buffer_size: " << current_occupy_buffer_size << endl;
                }
                if (drop_top_frame_when_network_change) {
                    while (!network_buffer_frames.empty()) {
                        NetworkBufferFrame &frame = network_buffer_frames.front();
                        dropped_frame_indexs.push_back(frame.frame_index);
                        cout << "Drop frame: " << frame.frame_index << " overall size: " << frame.frame_size <<  " frame.buffer_size: " << frame.buffer_size << " current_occupy_buffer_size: " << current_occupy_buffer_size << endl;
                        network_buffer_frames.erase(network_buffer_frames.begin());
                    }
                    while (network_buffer_size < current_occupy_buffer_size) {
                        NetworkBufferFrame &frame = network_buffer_frames.front();
                        current_occupy_buffer_size -= frame.buffer_size;
                        dropped_frame_indexs.push_back(frame.frame_index);
                        cout << "Drop frame: " << frame.frame_index << " overall size: " << frame.frame_size <<  " frame.buffer_size: " << frame.buffer_size << " current_occupy_buffer_size: " << current_occupy_buffer_size << endl;
                        network_buffer_frames.erase(network_buffer_frames.begin());
                    }
                }
                network_remain_buffer_size = network_buffer_size - current_occupy_buffer_size;
                if (ENABLE_LOG) {
                    cout << "Change network buffer size to: " << network_buffer_size << " network_remain_buffer_size: " << network_remain_buffer_size << " used_buffer_size:" << current_occupy_buffer_size << endl;
                }

                change_index = i_frame;
            } else if (enable_optimization && i_frame == target_frame_index - previous_drop_number) { // previously decrease the buffer size
                param.rc.i_vbv_buffer_size = current_bitrate / frame_rate * vbv; // kbit / 8 * 1000 = byte  // 100
                x264_encoder_reconfig(encoder, &param);
            }
        }
        // Recover vbv buffer size after network change
        if (enable_optimization && change_index != -1 && i_frame == change_index + 2) {
            cout << "Recover vbv buffer" << endl;
            param.rc.i_vbv_buffer_size = current_bitrate / frame_rate * default_vbv;
            x264_encoder_reconfig(encoder, &param);
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
        encode_duration += duration.count();

        // // Handle pacer buffer
        int temp = INT_MAX / 2;
        UpdateBufferFrames(network_buffer_frames, frame_send_receive_time_records, i_frame, i_frame_size * 8 / 1000, temp, INT_MAX / 2,
                           current_bitrate / (frame_rate * 0.9), dropped_frame_indexs, current_time_point, current_bitrate, display_time_point, send_frame_index_when_display,
                           frame_rate, drop_current_frame_when_buffer_full);
        current_time_point += each_frame_time;

        Statistics statistics;//{current_bitrate, i_frame_size, duration.count()};
        statistics.current_bitrate = current_bitrate * 1000 / (8 * frame_rate); // kbit to byte per frame
        statistics.frame_size = i_frame_size;
        statistics.duration = duration.count();
        statistics_result.push_back(statistics);

        if (WriteNALToFile(encoded_file_out, nal, i_frame_size) < 0) {
            cout << "WriteNALToFile failed" << endl;
            return;
        }
    }

    /* Flush  network_buffer_frames */
    while (!network_buffer_frames.empty()) {
        int temp = INT_MAX / 2;
        UpdateBufferFrames(network_buffer_frames, frame_send_receive_time_records, i_frame, -1, temp, INT_MAX / 2,
                           current_bitrate / (frame_rate * 0.9), dropped_frame_indexs, current_time_point, current_bitrate, display_time_point, send_frame_index_when_display,
                           frame_rate, drop_current_frame_when_buffer_full);
        current_time_point += each_frame_time;
    }

    /* Flush delayed frames */
    while (x264_encoder_delayed_frames(encoder)) {
        if (WriteNALToFile(encoded_file_out, nal, i_frame_size) < 0) {
            cout << "WriteNALToFile failed" << endl;
            return;
        }
    }

    x264_encoder_close(encoder);
    x264_picture_clean(&pic);

    OutputFrameSizeStatistics(statistics_result, frame_size_statistics_file);
    OutputRenderFrameIndex(dropped_frame_indexs, i_frame, render_frame_index_file);
    OutputDelayStatistics(frame_send_receive_time_records, delay_statistics_file);

    cout << endl << "--------------------------------------" << endl;
    cout << "encode_duration:" << encode_duration << endl;
    cout << "--------------------------------------" << endl << endl;

    fclose(input_yuv_file);
    fclose(encoded_file_out);
    fclose(bitrate_file);
}

int main() {
    // Basic configurations
    int frame_rate = 30;
    int initial_bitrate = 3000;
    int default_vbv = 15;
    int vbv = 1; // When vbv is 1, the actual frame size should not exceed the target
    int previous_drop_number = 0;
    bool drop_current_frame_when_buffer_full = true;

    string input_bitrate_config_filenames[3] = {"3000-1500", "3000-300", "3000-50"};

    // // change bitrate config
    // string filenames[4] = {"default_no_drop", "default_drop", "opt_no_drop", "opt_drop"};
    // bool configurations[4][2] = {{false, false}, {false, true}, {true, false}, {true, true}};

    // output filenames
    string output_filenames[2] = {"default", "opt"};

    EncodeAndGenerateStatistics("Gaming", "3000-50", "test", initial_bitrate, frame_rate, 1920, 1080, false, false, drop_current_frame_when_buffer_full, previous_drop_number, default_vbv, vbv);
    return 0;
    // Encode 720p videos
    int width = 1280;
    int height = 720;
    const string input_720p_yuv_filename = "Lecture720";
    EncodeAndGenerateStatistics(input_720p_yuv_filename, "static", "default", initial_bitrate, frame_rate, width, height, false, false, drop_current_frame_when_buffer_full, previous_drop_number, default_vbv, vbv);
    EncodeAndGenerateStatistics(input_720p_yuv_filename, "static", "opt", initial_bitrate, frame_rate, width, height, false, false, drop_current_frame_when_buffer_full, previous_drop_number, vbv, vbv);

    for (auto &input_bitrate_config_filename : input_bitrate_config_filenames) {
        bool enable_optimization = false;
        EncodeAndGenerateStatistics(input_720p_yuv_filename, input_bitrate_config_filename, "default", initial_bitrate, frame_rate, width, height, enable_optimization, false, drop_current_frame_when_buffer_full, previous_drop_number, default_vbv, vbv);
        enable_optimization = true;
        EncodeAndGenerateStatistics(input_720p_yuv_filename, input_bitrate_config_filename, "opt", initial_bitrate, frame_rate, width, height, enable_optimization, false, drop_current_frame_when_buffer_full, previous_drop_number, default_vbv, vbv);
    }

    // Encode 1080p videos
    width = 1920;
    height = 1080;
    string input_1080p_yuv_filenames[10] = {"Lecture1", "Lecture2", "Lecture3", "Lecture4", "Sports", "Sport2", "Animation1", "Animation2", "CoverSong", "Gaming"};
    for (auto &filename : input_1080p_yuv_filenames) {
        EncodeAndGenerateStatistics(filename, "static", "default", initial_bitrate, frame_rate, width, height, false, false, drop_current_frame_when_buffer_full, previous_drop_number, default_vbv, vbv);
        EncodeAndGenerateStatistics(filename, "static", "opt", initial_bitrate, frame_rate, width, height, false, false, drop_current_frame_when_buffer_full, previous_drop_number, vbv, vbv);
        for (auto &input_bitrate_config_filename : input_bitrate_config_filenames) {
            bool enable_optimization = false;
            EncodeAndGenerateStatistics(filename, input_bitrate_config_filename, "default", initial_bitrate, frame_rate, width, height, enable_optimization, false, drop_current_frame_when_buffer_full, previous_drop_number, default_vbv, vbv);
            enable_optimization = true;
            EncodeAndGenerateStatistics(filename, input_bitrate_config_filename, "opt", initial_bitrate, frame_rate, width, height, enable_optimization, false, drop_current_frame_when_buffer_full, previous_drop_number, default_vbv, vbv);
        }
    }

    return 0;
}
