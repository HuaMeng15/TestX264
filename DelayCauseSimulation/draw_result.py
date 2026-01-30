import os
import csv
from typing import Tuple, List, Dict

import matplotlib.pyplot as plt


def read_delays_csv_by_drop(path: str) -> Dict[float, Tuple[List[float], List[float]]]:
    """Read CSV with header rtt,drop_ratio,max_delay,... Return mapping drop_ratio -> (rtts, max_delays)."""
    if not os.path.exists(path):
        raise FileNotFoundError(path)
    data: Dict[float, List[Tuple[float, float]]] = {}
    with open(path, newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                rtt = float(row['rtt'])
                drop = float(row['drop_ratio'])
                maxd = float(row['max_delay'])
            except Exception:
                continue
            data.setdefault(drop, []).append((rtt, maxd))
    # sort entries by rtt
    out: Dict[float, Tuple[List[float], List[float]]] = {}
    for drop, lst in data.items():
        lst_sorted = sorted(lst, key=lambda x: x[0])
        rtts, maxd = zip(*lst_sorted)
        out[drop] = (list(rtts), list(maxd))
    return out


def plot_compare(group_csv: str, pure_csv: str, out_path: str = None):
    """Plot max delays in three subplots, one subplot per drop_ratio (compare group vs pure)."""
    group_map = read_delays_csv_by_drop(group_csv)
    pure_map = read_delays_csv_by_drop(pure_csv)

    drops = sorted(set(list(group_map.keys()) + list(pure_map.keys())))
    if not drops:
        raise RuntimeError("No data found in CSVs.")

    # take up to three drop ratios (user indicated three groups remain)
    drops_to_plot = drops[:3]

    if out_path is None:
        out_path = os.path.join(os.path.dirname(__file__), 'compare_max_delays_tailored_not_sharey.png')

    n = len(drops_to_plot)
    # share y axis so subplots use the same vertical scale
    fig, axes = plt.subplots(1, n, figsize=(5 * n, 4), sharey=False)
    if n == 1:
        axes = [axes]

    # collect global y range across the selected drops
    all_max_values = []
    for drop in drops_to_plot:
        if drop in group_map:
            _, maxd = group_map[drop]
            all_max_values.extend(maxd)
        if drop in pure_map:
            _, maxd_p = pure_map[drop]
            all_max_values.extend(maxd_p)
    ymin, ymax = None, None
    # if all_max_values:
    #     ymin = 0.0
    #     ymax = max(all_max_values) * 1.05
    # else:
    #     ymin, ymax = None, None

    for idx, drop in enumerate(drops_to_plot):
        ax = axes[idx]
        # plot group data if exists
        if drop in group_map:
            rtts, maxd = group_map[drop]
            ax.plot(rtts, maxd, label='group_packets', marker='o', color='C0', linestyle='-')
        # plot pure data if exists
        if drop in pure_map:
            rtts_p, maxd_p = pure_map[drop]
            ax.plot(rtts_p, maxd_p, label='pure_data', marker='s', color='C1', linestyle='--')

        ax.set_xlabel('RTT (ms)')
        ax.set_title(f'drop_ratio={int(drop)}')
        ax.grid(True)
        ax.legend()
        if ymin is not None and ymax is not None:
            ax.set_ylim(ymin, ymax)

    fig.supylabel('Max delay (ms)')
    fig.suptitle('Max delay comparison by drop_ratio (group vs pure)')
    plt.tight_layout(rect=[0, 0, 1, 0.95])
    plt.savefig(out_path, dpi=150)
    print(f'Comparison plot saved to: {out_path}')


if __name__ == '__main__':
    base = os.path.dirname(__file__)
    group_csv = os.path.join(base, 'group_packets_delays.csv')
    pure_csv = os.path.join(base, 'pure_dataflow_delays.csv')
    plot_compare(group_csv, pure_csv)

