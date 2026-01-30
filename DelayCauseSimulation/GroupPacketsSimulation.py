import os
import math
from typing import List, Tuple

import numpy as np
import matplotlib.pyplot as plt


PacketBits = 1500 * 8  # 1500 bytes
fps = 30

def simulate(t_drop: int, t_end: int, rtt: int, rate_before: int, rate_after: int, utilization: float) -> List[float]:
    delays = []
    accumulated_delay = 0
    propogation_delay = rtt / 2
    interval = 1000 / fps
    interval = round(interval, 3)
    t_react = t_drop + interval + rtt
    t = 0

    while t < t_end:        
        encoded_rate = rate_before if t < t_react else rate_after
        frame_size = encoded_rate * utilization / fps
        
        send_out_rate = rate_before if t < t_drop else rate_after
        transmission_delay = frame_size / send_out_rate * 1000.0
        transmission_delay = round(transmission_delay, 3)
        
        # print(f'encoded_rate: {encoded_rate}, send_out_rate: {send_out_rate}, frame_size: {frame_size}')
        
        if transmission_delay > interval:
            accumulated_delay += transmission_delay - interval
        else:
            accumulated_delay -= interval - transmission_delay
            if accumulated_delay < 0:
                accumulated_delay = 0

        delays.append(propogation_delay + transmission_delay + accumulated_delay)
        # print(f't: {t}, interval: {interval}, transmission_delay: {transmission_delay}, accumulated_delay: {accumulated_delay}, delay: {propogation_delay + transmission_delay + accumulated_delay}')
        t += interval
        t = round(t, 3)
    return delays

def run_experiments():
    rate_before = 30e6  # 30 Mbps
    utilization = 0.9
    t_drop = 2000 		# bandwidth drops at 2s
    t_end = 7000 		# end at 7s
    
    result_file = f'group_packets_delays.csv'
    f_result_file = open(result_file, 'w')
    f_result_file.write('rtt,drop_ratio,max_delay,p99_delay,p999_delay\n')

    # RTTs to sweep (milliseconds)
    rtt_ms = [10, 20, 30, 50, 100, 200]
    drop_ratios = [2, 3, 5, 10]
    
    for drop_ratio in drop_ratios:
        rate_after = rate_before / drop_ratio
        max_delays = []
        p99_delays = []
        p999_delays = []
        
        for rtt in rtt_ms:
            delays = simulate(t_drop, t_end, rtt, rate_before, rate_after, utilization)
            # exit(0)
            if len(delays) == 0:
                max_delays.append(0.0)
                p99_delays.append(0.0)
                p999_delays.append(0.0)
                continue
            arr = np.array(delays)
            max_delay = np.max(arr)
            p99_delay = np.percentile(arr, 99)
            p999_delay = np.percentile(arr, 99.9)
            max_delays.append(max_delay)
            p99_delays.append(p99_delay)
            p999_delays.append(np.percentile(arr, 99.9))
            f_result_file.write(f'{rtt},{drop_ratio},{max_delay},{p99_delay},{p999_delay}\n')

        # plot
        plt.figure(figsize=(8, 5))
        rtt_plot_ms = rtt_ms
        plt.plot(rtt_plot_ms, max_delays, label='max delay (ms)', marker='o')
        plt.plot(rtt_plot_ms, p99_delays, label='99th percentile (ms)', marker='o')
        plt.plot(rtt_plot_ms, p999_delays, label='99.9th percentile (ms)', marker='o')
        plt.xlabel('RTT (ms)')
        plt.ylabel('Delay (ms)')
        plt.title('Delays vs RTT for a group packets simulation with bandwidth drop 30Mbps -> 3Mbps')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        out = os.path.join(os.path.dirname(__file__), f'group_packets_delays_{rate_before/1e6}_{rate_after/1e6}.png')
        plt.savefig(out, dpi=150)
        print(f'Plot saved to: {out}')


if __name__ == '__main__':
    run_experiments()