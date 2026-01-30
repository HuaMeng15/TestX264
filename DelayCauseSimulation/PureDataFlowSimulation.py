import os
import math
from typing import List, Tuple

import numpy as np
import matplotlib.pyplot as plt


PacketBits = 1500 * 8  # 1500 bytes

def simulate(t_drop: int, t_react, t_end: int, rtt: int, rate_before: int, rate_after: int, utilization: float) -> List[float]:
    delays = []
    accumulated_delay = 0
    propogation_delay = rtt / 2
    t = 0

    while t < t_end:
        send_interval_rate = rate_before if t < t_react else rate_after
        interval = (PacketBits / (send_interval_rate * utilization)) * 1000.0
        interval = round(interval, 3)
        
        send_out_rate = rate_before if t < t_drop else rate_after
        transmission_delay = PacketBits / send_out_rate * 1000.0
        transmission_delay = round(transmission_delay, 3)
        
        if transmission_delay > interval:
            accumulated_delay += transmission_delay - interval
        else:
            accumulated_delay -= interval - transmission_delay
            if accumulated_delay < 0:
                accumulated_delay = 0
        if t > 1900 and t < 2500:
            print(f't: {t}, interval: {interval}, propogation_delay: {propogation_delay}, transmission_delay: {transmission_delay}, accumulated_delay: {accumulated_delay}, delay: {propogation_delay + transmission_delay + accumulated_delay}')

        delays.append(propogation_delay + transmission_delay + accumulated_delay)
        t += interval
        t = round(t, 3)
    return delays

def run_experiments():
    rate_before = 30e6  # 30 Mbps
    utilization = 0.9
    t_drop = 2000 		# bandwidth drops at 2s
    t_end = 7000 		# end at 7s
    
    result_file = f'pure_dataflow_delays.csv'
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
            print(f'\n\n----------------Running {rtt}ms, {drop_ratio}x drop ratio----------------\n\n')
            t_react = t_drop + rtt  # sender reacts after at least one RTT
            delays = simulate(t_drop, t_react, t_end, rtt, rate_before, rate_after, utilization)
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
        plt.title('Delays vs RTT for a pure data flow with bandwidth drop 30Mbps -> 3Mbps')
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        out = os.path.join(os.path.dirname(__file__), f'pure_dataflow_delays_{rate_before/1e6}_{rate_after/1e6}.png')
        plt.savefig(out, dpi=150)
        print(f'Plot saved to: {out}')


if __name__ == '__main__':
    run_experiments()