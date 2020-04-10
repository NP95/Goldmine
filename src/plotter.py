import matplotlib

matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties

from matplotlib.ticker import MultipleLocator, FormatStrFormatter

matplotlib.rcParams.update({'font.size': 25})
fontP = FontProperties()
fontP.set_size('larger')

def x_y_plot(importance, complexity, module, output, metric_a, metric_b, PICPATH):

    fig, ax = plt.subplots(figsize=(8,4))
    ax.plot(importance, complexity, 'bo')
    ax.grid(b=True, which='major', color='black', linestyle='--', linewidth = 1)

    ax.set_xlabel(metric_a + ' of assertions', fontsize=17, fontweight='bold')
    ax.set_ylabel(metric_b + ' of assertions', fontsize=17, fontweight='bold')
    ax.tick_params('y', labelsize=15)
    ax.tick_params('x', labelsize=15)

    fig.tight_layout()

    plt.savefig(PICPATH + '/' + module + '_' + output + '_' + metric_a + '_' + \
        metric_b + '.pdf')
    plt.savefig(PICPATH + '/' + module + '_' + output + '_' + metric_a + '_' + \
        metric_b + '.png')
    
    plt.close(fig)
