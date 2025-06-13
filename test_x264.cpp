#include "stdint.h"
#include "x264.h"
#include "x264_config.h"
#include <iostream>
#include <filesystem>
#include <string.h>
// Time Analysis
#include <chrono>
#include <vector>
#include <thread> // For std::this_thread::sleep_for
#include <mutex>
#include <fstream>
#include <condition_variable>

using namespace std;

#define QP 21 // Used when CQP
#define PRESET "superfast"

const bool ENABLE_LOG = true;
const string FILE_PREFIX = "/home/eceuser/menghua/Research/TestX264/";
const double REDUCE_RATIO = 0.8;

void InitEncodeParam(x264_param_t &param, int &initial_bitrate, int frame_rate, int width, int height, double vbv_buffer_size) {
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
    initial_bitrate = initial_bitrate * REDUCE_RATIO;
    param.rc.i_bitrate = initial_bitrate;

    param.rc.i_vbv_max_bitrate = initial_bitrate;

    param.rc.i_vbv_buffer_size = initial_bitrate * vbv_buffer_size; // kbit / 8 * 1000 = byte

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

void UpdateBitrateConfig(x264_t *encoder, x264_param_t &param, int bitrate, double vbv_buffer_size) {
    bitrate = bitrate * REDUCE_RATIO;
    cout << "Reconfig to bitrate:" << bitrate << endl;
    param.rc.i_bitrate = bitrate;
    param.rc.i_vbv_max_bitrate = bitrate;
    param.rc.i_vbv_buffer_size = bitrate * vbv_buffer_size;

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

std::string doubleToString(double value) {
    std::ostringstream out;
    if (value >= 0.1) {
        out << std::fixed << std::setprecision(1) << value; // Set fixed format and 1 decimal places
    } else {
        out << std::fixed << std::setprecision(2) << value; // Set fixed format and 2 decimal places
    }
    return out.str(); // Convert to string
}
struct NetworkBufferFrame {
    int frame_index;
    int frame_size;
    int buffer_size;
};

std::vector<NetworkBufferFrame> network_buffer_frames;
std::mutex buffer_mtx;
int current_bitrate = 0;
std::mutex bitrate_mtx;
std::mutex send_finish_mtx;
std::mutex receive_finish_mtx;
bool send_finished = false;
bool receive_finished = false;
std::condition_variable receive_finished_cv;
std::condition_variable send_one_frame_cv;

void ReduceNetworkBufferFrame(int transmitted_size, std::ofstream &out_file) {
    NetworkBufferFrame &frame = network_buffer_frames.front();
    if (frame.buffer_size > transmitted_size) {
        frame.buffer_size -= transmitted_size;
        auto now = std::chrono::high_resolution_clock::now();
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();
        if (out_file.is_open()) {
            // out_file << ms << " frame: " << frame.frame_index << " size: " << frame.frame_size << " remain size: " << frame.buffer_size << endl;
        }
    } else {
        transmitted_size -= frame.buffer_size;
        auto now = std::chrono::high_resolution_clock::now();
        // Convert to milliseconds since epoch
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();
        if (out_file.is_open()) {
            out_file << ms << " Finish Transmitting frame:" << frame.frame_index << " frame_size:" << frame.frame_size << std::endl;
        }
        network_buffer_frames.erase(network_buffer_frames.begin());
    }
    // out_file << "Transmitted size: " << transmitted_size << endl;
}

void TransmitNetworkBuffer(const string& receive_log) {
    std::ofstream out_file(receive_log);
    while (true) {
        // cout << "Waiting for network buffer... send_finished: " << send_finished << endl;
        std::unique_lock<std::mutex> lock(buffer_mtx);
        send_one_frame_cv.wait(lock, [] { return (send_finished == true || !network_buffer_frames.empty()); });
        while (!network_buffer_frames.empty()) {
            int transmitted_size = current_bitrate / 8; // Convert to bytes in 1ms
            ReduceNetworkBufferFrame(transmitted_size, out_file);
            std::this_thread::sleep_for(std::chrono::milliseconds(1));
        }
        if (send_finished && network_buffer_frames.empty()) {
            std::cout << "Finished transmitting." << std::endl;
            {
                std::lock_guard<std::mutex> lock(receive_finish_mtx);
                receive_finished = true;
            }
            break;
        }
    }
    receive_finished_cv.notify_one();
    out_file.close();
}

void EncodeAndGenerateStatistics(const string &video_name, const string &bitrate_config_filename, const string &output_dir, int initial_bitrate, int frame_rate, int width, int height, double vbv_buffer_size, int response_time, const string &suffix) {
    x264_param_t param;
    x264_t *encoder;
    x264_picture_t pic;
    x264_picture_t pic_out;
    int i_frame = 0;
    int i_frame_size;
    x264_nal_t *nal;
    int i_nal;

    string send_log_file = output_dir + "send.log";
    string bitrate_config_file =  FILE_PREFIX + "input/bitrate_config/" + bitrate_config_filename;
    string input_video_file = FILE_PREFIX + "input/" + video_name + ".yuv";
    string output_video_file = output_dir + "result.mkv";

    InitEncodeParam(param, initial_bitrate, frame_rate, width, height, vbv_buffer_size);

    if (!std::filesystem::is_directory(output_dir)) {
        cout << "Create directory: " <<  output_dir << endl;
        std::filesystem::create_directory(output_dir);
    }

    FILE *input_yuv_file = fopen(input_video_file.c_str(), "rb");
    FILE *encoded_file_out = fopen(output_video_file.c_str(), "wb");
    FILE *bitrate_file = fopen(bitrate_config_file.c_str(), "rb");
    std::ofstream send_file(send_log_file);
    if (!input_yuv_file || !encoded_file_out || !bitrate_file) {
        cout << "fopen failed input_yuv_file:" << !input_yuv_file << " encoded_file_out:" << !encoded_file_out << " bitrate_file: " << !bitrate_file << endl;
        return;
    }

    vector<BitrateConfig> bitrate_config_vec;
    ReadBitrateConfig(bitrate_file, bitrate_config_vec);

    cout << "param i_bitrate: " << param.rc.i_bitrate << " max_bitrate: " << param.rc.i_vbv_max_bitrate << " vbv_buffer_size: " << param.rc.i_vbv_buffer_size << endl;

    if(x264_picture_alloc( &pic, param.i_csp, param.i_width, param.i_height) < 0 ) {
        cout << "x264_picture_alloc failed" << endl;
        return;
    }

    encoder = x264_encoder_open(&param);
    if( !encoder ) return;

    int luma_size = param.i_width * param.i_height;
    int chroma_size = luma_size / 4;

    /* Encode frames */
    {
        // std::lock_guard<std::mutex> lock(bitrate_mtx);
        current_bitrate = initial_bitrate;
    }
    int bitrate_config_index = 0;
    int drop_period_frames = 0;

    for(;; i_frame++) {
        // Update bitrate
        if (bitrate_config_index < bitrate_config_vec.size()) {
            if (i_frame == bitrate_config_vec[bitrate_config_index].start_frame_index + response_time) {
                {
                    // std::lock_guard<std::mutex> lock(bitrate_mtx);
                    current_bitrate = bitrate_config_vec[bitrate_config_index].bitrate;
                }
                double vbv_ratio = vbv_buffer_size;

                bitrate_config_index++;
                if (suffix == "_adaptive_") {
                    if (i_frame != response_time) {
                    // Reduce vbv_buffer_size for 10 frames
                    drop_period_frames = 10;
                    if (vbv_ratio > 0.5) {
                        vbv_ratio = 0.1;
                    } else {
                        vbv_ratio = 0.04;
                    }
                    cout << "Update drop_period_frames: " << drop_period_frames << endl;
                }
                }
                UpdateBitrateConfig(encoder, param, current_bitrate, vbv_ratio);
                cout << "Update bitrate at frame" << i_frame << " Current bitrate: " << current_bitrate << " codec bitrate: " << param.rc.i_bitrate << " vbv_buffer_size: " << param.rc.i_vbv_buffer_size << endl;
            }
        }
        if (drop_period_frames > 0) {
            drop_period_frames--;
            if (drop_period_frames == 0) {
                UpdateBitrateConfig(encoder, param, current_bitrate, vbv_buffer_size);
                cout << "Update bitrate at frame" << i_frame << " Current bitrate: " << current_bitrate << " codec bitrate: " << param.rc.i_bitrate << " vbv_buffer_size: " << param.rc.i_vbv_buffer_size << endl;
            }
        }
        /* Read input frame */
        auto encode_start = chrono::high_resolution_clock::now();
        if (fread(pic.img.plane[0], 1, luma_size, input_yuv_file) != (unsigned)luma_size) break;
        if (fread(pic.img.plane[1], 1, chroma_size, input_yuv_file) != (unsigned)chroma_size) break;
        if (fread(pic.img.plane[2], 1, chroma_size, input_yuv_file) != (unsigned)chroma_size) break;

        pic.i_pts = i_frame;

        i_frame_size = x264_encoder_encode(encoder, &nal, &i_nal, &pic, &pic_out);

        if (WriteNALToFile(encoded_file_out, nal, i_frame_size) < 0) {
            cout << "WriteNALToFile failed" << endl;
            return;
        }

        auto encode_end = chrono::high_resolution_clock::now();
        auto encode_duration = chrono::duration_cast<chrono::milliseconds>(encode_end - encode_start);
        int encoded_duration = encode_duration.count();

        auto now = std::chrono::high_resolution_clock::now();
        // Convert to milliseconds since epoch
        auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(now.time_since_epoch()).count();
        send_file << ms << " Encode frame:" << i_frame + 1 << " frame_size:" << i_frame_size << std::endl;

        if (i_frame > 0) {
            network_buffer_frames.push_back({i_frame + 1, i_frame_size, i_frame_size});
        }
        // send_one_frame_cv.notify_one();

        // std::this_thread::sleep_for(std::chrono::milliseconds(1000 / frame_rate - encoded_duration));
    }

    /* Flush delayed frames */
    while (x264_encoder_delayed_frames(encoder)) {
        if (WriteNALToFile(encoded_file_out, nal, i_frame_size) < 0) {
            cout << "WriteNALToFile failed" << endl;
            return;
        }
    }

    // {
    //     std::lock_guard<std::mutex> lock(send_finish_mtx);
    //     send_finished = true;
    // }
    // send_one_frame_cv.notify_one();

    x264_encoder_close(encoder);
    x264_picture_clean(&pic);

    fclose(input_yuv_file);
    fclose(encoded_file_out);
    fclose(bitrate_file);

    std::unique_lock<std::mutex> lock(receive_finish_mtx);
    send_one_frame_cv.wait(lock, [] { return receive_finished = true; });
}

int main(int argc, char* argv[]) {
    if (argc < 7) {
        std::cerr << "Invalid arguments." << std::endl;
        return 1; // Return an error code
    }
    string video_name = argv[1];
    string bitrate_filename = argv[2];
    char* end;
    double vbv_buffer_size = std::strtod(argv[3], &end);
    string output_dir = argv[4];
    int response_time = std::strtod(argv[5], &end);
    string suffix = argv[6];
    cout << "bitrate_filename:" << bitrate_filename << " vbv_buffer_size:" << vbv_buffer_size << endl;
    cout << "output_dir:" << output_dir << " response_time:" << response_time << endl;
    // return 0;

    // Basic configurations
    int frame_rate = 30;
    int initial_bitrate = 10000;
    int width = 1920;
    int height = 1080;

    // std::thread encode_thread(EncodeAndGenerateStatistics, video_name, bitrate_filename, output_dir, initial_bitrate, frame_rate, width, height, vbv_buffer_size);
    // string receive_log_file = output_dir + "receive.log";
    // std::thread transmit_thread(TransmitNetworkBuffer, receive_log_file);

    // encode_thread.join();
    // transmit_thread.join();

    EncodeAndGenerateStatistics(video_name, bitrate_filename, output_dir, initial_bitrate, frame_rate, width, height, vbv_buffer_size, response_time, suffix);

    return 0;
}
