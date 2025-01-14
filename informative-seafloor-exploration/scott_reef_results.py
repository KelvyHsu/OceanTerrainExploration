import numpy as np
import shelve
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import cm
import logging
import time
import matplotlib.ticker as ticker

def main():

    main_directory = "../../../Thesis/Results/scott-reef/"

    # Comparing different starting locations
    def compare_starting_locations():

        directory0 = main_directory + 'loc1_new_20150827_072158__method_LDE_start_377500_8440000_hsteps30_horizon5000/'
        directory1 = main_directory + 'loc2_new_20150827_163015__t200_q100000_ts250_qs500_method_LDE_start380000.08440000.0_hsteps30_horizon5000.0/'
        directory2 = main_directory + 'loc3_20150816_232942__t200_q100000_ts250_qs500_method_LDE_start375000_8445000_hsteps30_horizon5000/'
        directory3 = main_directory + 'loc4_20150817_214222__t200_q100000_ts250_qs500_method_LDE_start365000_8445000_hsteps30_horizon5000/'
        directory4 = main_directory + 'loc5_20150819_235323__t200_q100000_ts250_qs500_method_LDE_start380000_8446000_hsteps30_horizon5000/'

        data0 = obtain_data(directory0, {'index': 0, 'label': 'Location 1', 'steps': 200})
        data1 = obtain_data(directory1, {'index': 1, 'label': 'Location 2', 'steps': 200})
        data2 = obtain_data(directory2, {'index': 2, 'label': 'Location 3', 'steps': 200})
        data3 = obtain_data(directory3, {'index': 3, 'label': 'Location 4', 'steps': 200})
        data4 = obtain_data(directory3, {'index': 4, 'label': 'Location 5', 'steps': 200})

        plot_data(main_directory, data0, data1, data2, data3, data4, ncolors = 5, descript = 'locations', label_font_size = 28, ncol = 5)
        logging.info('Compared starting locations')

    # Comparing different horizons
    def compare_horizons():

        directory0 = main_directory + 'loc1_new_20150827_072158__method_LDE_start_377500_8440000_hsteps30_horizon5000/'
        directory1 = main_directory + 'h_compare_20150815_062732__t200_q100000_ts250_qs500_method_LDE_start375000.08440000.0_hsteps30_horizon7500.0/'
        directory2 = main_directory + 'h_compare_20150815_062834__t200_q100000_ts250_qs500_method_LDE_start375000.08440000.0_hsteps30_horizon6000.0/'

        data0 = obtain_data(directory0, {'index': 0, 'label': 'Horizon: 5000 m', 'steps': 200})
        data1 = obtain_data(directory1, {'index': 1, 'label': 'Horizon: 7500 m', 'steps': 200})
        data2 = obtain_data(directory2, {'index': 2, 'label': 'Horizon: 6000 m', 'steps': 200})

        plot_data(main_directory, data0, data1, data2, ncolors = 3, descript = 'horizons', label_font_size = 36)
        logging.info('Compared horizons')

    # Compare with other methods
    def compare_methods():

        directory00 = main_directory + 'loc1_new_20150827_072158__method_LDE_start_377500_8440000_hsteps30_horizon5000/'
        directory01 = main_directory + 'loc2_new_20150827_163015__t200_q100000_ts250_qs500_method_LDE_start380000.08440000.0_hsteps30_horizon5000.0/'
        directory10 = main_directory + 'loc_20150816_015647__t200_q100000_ts250_qs500_method_MIE_GREEDY_start377500.08440000.0_hsteps30_horizon5000.0/'
        directory11 = main_directory + 'loc_20150816_015641__t200_q100000_ts250_qs500_method_MIE_GREEDY_start380000.08440000.0_hsteps30_horizon5000.0/'
        directory20 = main_directory + 'loc_20150816_064319__t200_q100000_ts250_qs500_method_RANDOM_start377500.08440000.0_hsteps30_horizon5000.0/'
        directory21 = main_directory + 'loc_20150816_081923__t200_q100000_ts250_qs500_method_RANDOM_start380000.08440000.0_hsteps30_horizon5000.0/'
        directory30 = main_directory + 'loc1_new_20150827_072830__method_MCJE_start_377500_8440000_hsteps30_horizon5000/'
        directory31 = main_directory + 'loc_20150821_085829__t200_q100000_ts250_qs500_method_MCJE_start380000.08440000.0_hsteps30_horizon5000.0/'
        directory40 = main_directory + 'loc_20150818_085143__t200_q100000_ts250_qs500_method_MIE_start377500.08440000.0_hsteps30_horizon5000.0/'
        directory41 = main_directory + 'loc_20150818_221107__t200_q100000_ts250_qs500_method_MIE_start380000.08440000.0_hsteps30_horizon5000.0/'
        directory50 = main_directory + 'loc_20150822_141334__t200_q100000_ts250_qs500_method_FIXED_start377500.08440000.0_hsteps30_horizon5000.0/'
        directory51 = main_directory + 'loc_20150818_120403__t200_q100000_ts250_qs500_method_FIXED_start380000.08440000.0_hsteps30_horizon5000.0/'
        directory60 = main_directory + 'loc_20150819_095126__t200_q100000_ts250_qs500_method_FIXED_start377500.08440000.0_hsteps30_horizon5000.0/'
        directory61 = main_directory + 'loc_20150819_095211__t200_q100000_ts250_qs500_method_FIXED_start380000.08440000.0_hsteps30_horizon5000.0/'

        data00 = obtain_data(directory00, {'index': 0, 'label': 'Location 1 with LMDE', 'steps': 200})
        data01 = obtain_data(directory01, {'index': 0, 'label': 'Location 2 with LMDE', 'steps': 200, 'linestyle': 'dashed'})
        data10 = obtain_data(directory10, {'index': 1, 'label': 'Location 1 with GREEDY-PIE', 'steps': 200})
        data11 = obtain_data(directory11, {'index': 1, 'label': 'Location 2 with GREEDY-PIE', 'steps': 200, 'linestyle': 'dashed'})
        data20 = obtain_data(directory20, {'index': 2, 'label': 'Location 1 with RANDOM', 'steps': 200})
        data21 = obtain_data(directory21, {'index': 2, 'label': 'Location 2 with RANDOM', 'steps': 200, 'linestyle': 'dashed'})
        data30 = obtain_data(directory30, {'index': 3, 'label': 'Location 1 with MCPIE', 'steps': 200})
        data31 = obtain_data(directory31, {'index': 3, 'label': 'Location 2 with MCPIE', 'steps': 200, 'linestyle': 'dashed'})
        data40 = obtain_data(directory40, {'index': 4, 'label': 'Location 1 with AMPIE', 'steps': 200})
        data41 = obtain_data(directory41, {'index': 4, 'label': 'Location 2 with AMPIE', 'steps': 200, 'linestyle': 'dashed'})
        data50 = obtain_data(directory50, {'index': 5, 'label': 'Location 1 with SPIRAL', 'steps': 200})
        data51 = obtain_data(directory51, {'index': 5, 'label': 'Location 2 with SPIRAL', 'steps': 200, 'linestyle': 'dashed'})
        data60 = obtain_data(directory60, {'index': 6, 'label': 'Location 1 with LINES', 'steps': 200})
        data61 = obtain_data(directory61, {'index': 6, 'label': 'Location 2 with LINES', 'steps': 200, 'linestyle': 'dashed'})

        plot_data(main_directory, data00, data01, data10, data11, data20, data21, data30, data31, data40, data41, data50, data51, data60, data61, ncolors = 7, descript = 'methods', label_font_size = 20.5)

        logging.info('Compared methods')
        rank_data(data00, data01, data10, data11, data20, data21, data30, data31, data40, data41, data50, data51, data60, data61)

    logging.basicConfig(level = logging.DEBUG)

    compare_starting_locations()
    compare_horizons()
    compare_methods()

    plt.show()

def rank_data(*args):

    performances = np.array([arg[0][arg[-1].get('steps') - 1] for arg in args])
    names = [arg[-1].get('label') for arg in args]
    ind = performances.argsort()
    table = [(names[i], np.round(100 * performances[i], 2)) for i in ind]
    [print(t) for t in table]
    print('----------')
    [print(t) for t in table if 'Location 1' in t[0]]
    print('----------')
    [print(t) for t in table if 'Location 2' in t[0]]

def obtain_data(directory, info):

    try:
        history = np.load('%shistory.npz' % directory)
        miss_ratio_array = history['miss_ratio_array']
        yq_lde_mean_array = history['yq_lde_mean_array']
        yq_mie_mean_array = history['yq_mie_mean_array']
        logging.info('Obtained data for {0}'.format(info))
    except:
        miss_ratio_array = np.nan * np.ones(info['steps'])
        yq_lde_mean_array = np.nan * np.ones(info['steps'])
        yq_mie_mean_array = np.nan * np.ones(info['steps'])
        logging.info('Failed to obtain data for {0}'.format(info))
    return miss_ratio_array, yq_lde_mean_array, yq_mie_mean_array, info

def fig_size(fig_width_pt):
    inches_per_pt = 1.0/72.27               # Convert pt to inch
    golden_mean = (np.sqrt(5) - 1.0)/2.0    # Aesthetic ratio
    fig_width = fig_width_pt * inches_per_pt# width in inches
    fig_height = fig_width * golden_mean    # height in inches
    return fig_width, fig_height

def plot_data(directory, *args, ncolors = 1, descript = '', label_font_size = 24, ncol = 4):

    L = 0.0
    colors = cm.rainbow(np.linspace(0 + L, 1 - L, num = ncolors))

    fontsize = 64
    axis_tick_font_size = 30
    
    params = {
        'backend': 'ps',
        # 'axes.labelsize': 10,
        # 'text.fontsize': 10,
        # 'legend.fontsize': 10,
        # 'xtick.labelsize': 8,
        # 'ytick.labelsize': 8,
        'text.usetex': True,
        'figure.figsize': fig_size(350.0)
    }

    plt.rc_context(params)

    fig = plt.figure(figsize = (20, 15))
    ax1 = fig.add_subplot(211)
    # ax2 = fig.add_subplot(312)
    ax3 = fig.add_subplot(212)

    mission_starts = np.array([40, 80, 120, 160, 200]) * (5000.0/30.0)
    [ax1.axvline(x, color = 'k', linestyle = '--') for x in mission_starts]
    [ax3.axvline(x, color = 'k', linestyle = '--') for x in mission_starts]

    percentages = np.arange(0, 100, 10)
    [ax1.axhline(y, color = 'k', linestyle = '--') for y in percentages]
    entropies = np.arange(1.4, 2.2, 0.2)
    [ax3.axhline(y, color = 'k', linestyle = '--') for y in entropies]

    for arg in args:

        miss_ratio_array, yq_lde_mean_array, yq_mie_mean_array, info = arg

        iterations = np.arange(miss_ratio_array.shape[0]) + 1
        
        color = colors[info['index']]
        label = info['label']
        steps = info['steps']
        if 'linestyle' in info:
            linestyle = info['linestyle']
        else:
            linestyle = 'solid'

        iterations_plt = np.append(0, iterations[:steps]) * (5000.0/30.0)
        miss_ratio_plt = np.append(41.54, 100 * miss_ratio_array[:steps])
        yq_lde_plt = np.append(-1.03, yq_lde_mean_array[:steps])
        yq_mie_plt = np.append(2.14, yq_mie_mean_array[:steps])

        ax1.plot(iterations_plt, miss_ratio_plt, c = color, label = label, linewidth = 2.0, linestyle = linestyle)
        ax1.set_ylim((0, 50))
        # ax2.plot(iterations_plt, yq_lde_plt, c = color, label = label, linewidth = 2.0, linestyle = linestyle)
        ax3.plot(iterations_plt, yq_mie_plt, c = color, label = label, linewidth = 2.0, linestyle = linestyle)

    ax1.legend(bbox_to_anchor = (0., 0.0, 1., .05), loc = 3,
           ncol = ncol, borderaxespad = 0., fontsize = label_font_size)

    ax1.set_title('Percentage of Map Prediction Misses', fontsize = fontsize)
    ax1.set_ylabel('Misses (\%)', fontsize = fontsize)
    ax1.set_xticklabels( () )

    # ax2.set_title('Average Marginalised L. Model Differential Entropy', fontsize = fontsize)
    # ax2.set_ylabel('Entropy (nats)', fontsize = fontsize)
    # ax2.set_xticklabels( () )

    ax3.set_title('Avg. Marg. Prediction Information Entropy', fontsize = fontsize)
    ax3.set_ylabel('Entropy (nats)', fontsize = fontsize)
    ax3.get_xaxis().get_major_formatter().set_useOffset(False)
    ax3.set_xlabel('Distance Traveled (km)', fontsize = fontsize)

    for tick in ax1.yaxis.get_major_ticks():
        tick.label.set_fontsize(axis_tick_font_size)
    # for tick in ax2.yaxis.get_major_ticks():
    #     tick.label.set_fontsize(axis_tick_font_size)
    for tick in ax3.xaxis.get_major_ticks():
        tick.label.set_fontsize(axis_tick_font_size)
    for tick in ax3.yaxis.get_major_ticks():
        tick.label.set_fontsize(axis_tick_font_size)

    # ticks = ticker.FuncFormatter(lambda x, pos: '{0:g}'.format(x/1e3))
    # ax3.xaxis.set_major_formatter(ticks)
    # ax3.yaxis.set_major_formatter(ticks)

    # Save the plot
    fig.tight_layout()
    fig.savefig('%scompare_%s.eps' % (directory, descript))

if __name__ == "__main__":
    main()