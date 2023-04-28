#from settings import settings
import numpy as np
import matplotlib.pyplot as pp

def plotMeasure(series, width=6, height=0.5):
    fig, ax = pp.subplots()
    for i, label in enumerate(series.keys()):
        t = 0
        times = []
        for msg in series[label]:
            t += msg.time
            times.append(t)
        ax.plot(times, np.zeros_like(times) + i, '|', markersize=10, label=label)
    ax.set_yticks(range(len(series)))
    ax.set_yticklabels(list(series.keys()), fontsize=12)
    ax.tick_params(axis='both', labelsize=12)
    ax.autoscale(enable=True, axis='x', tight=True)
    fig.set_size_inches(width, len(series) * height)
    pp.subplots_adjust(left=0.2, right=0.95, top=0.95, bottom=0.1)
    pp.xlabel('Time', fontsize=14)
    pp.show()

