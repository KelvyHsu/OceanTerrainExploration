import numpy as np
import shelve
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import cm
import logging
import time

def main():

    main_directory = '../Figures/'

    # Batch 1: Laptop
    # directory0 = main_directory + 'small_patches_lde/'
    # directory1 = main_directory + 'small_patches_mie/'
    # directory2 = main_directory + 'small_patches_greedy/'
    # directory3 = main_directory + 'small_patches_random_1/'
    # directory4 = main_directory + 'small_patches_random_2/'

    # Batch 2: Laptop
    # directory0 = main_directory + 'batch2---start-0.1+0.2-seed100-e30-range2.5-classes4-steps300-st-methodLE/'
    # directory1 = main_directory + 'batch2---start-0.1+0.2-seed100-e30-range2.5-classes4-steps300-st-methodMIE/'
    # directory2 = main_directory + 'batch2---start-0.1+0.2-seed100-e30-range2.5-classes4-steps300-st-methodGREEDY/'
    # directory3 = main_directory + 'batch2---start-0.1+0.2-seed100-e30-range2.5-classes4-steps300-st-methodRANDOM1/'
    # directory4 = main_directory + 'batch2---start-0.1+0.2-seed100-e30-range2.5-classes4-steps300-st-methodRANDOM2/'

    # Batch 3: Desktop
    directory0 = main_directory + 'batch3---start-1.0-1.0-seed100-e30-range2.5-classes4-steps300-st-methodLE/'
    directory1 = main_directory + 'batch3---start-1.0-1.0-seed100-e30-range2.5-classes4-steps300-st-methodMIE/'
    directory2 = main_directory + 'batch3---start-1.0-1.0-seed100-e30-range2.5-classes4-steps300-st-methodGREEDY/'
    directory3 = main_directory + 'batch3---start-1.0-1.0-seed100-e30-range2.5-classes4-steps300-st-methodRANDOM-chaos1/'
    directory4 = main_directory + 'batch3---start-1.0-1.0-seed100-e30-range2.5-classes4-steps300-st-methodRANDOM-chaos2/'

    data0 = obtain_data(directory0, (0, 'RHIE with Linearised Differential Entropy (LDE)'))
    data1 = obtain_data(directory1, (1, 'RHIE with Marginalised Information Entropy (MIE)'))
    data2 = obtain_data(directory2, (2, 'Greedy Exploration with MIE'))
    data3 = obtain_data(directory3, (3, 'Open Loop Explorer 1'))
    data4 = obtain_data(directory4, (4, 'Open Loop Explorer 2'))
    plot_data(main_directory, data0, data1, data2, data3, data4)

    plt.show()

# def main():

#     main_directory = '../Figures/'
#     directory_lde0 = main_directory + 'lde_000/'
#     directory_lde1 = main_directory + 'lde_100/'
#     directory_lde2 = main_directory + 'lde_200/'

#     directory_mie0 = main_directory + 'mie_000/'
#     directory_mie1 = main_directory + 'mie_100/'
#     directory_mie2 = main_directory + 'mie_200/'

#     directory_greed0 = main_directory + 'greed_000/'
#     directory_greed1 = main_directory + 'greed_100/'
#     directory_greed2 = main_directory + 'greed_200/'

#     # convert_old_to_new_format(directory0, directory1, directory2)

#     data_lde0 = obtain_data(directory_lde0, 0)
#     data_lde1 = obtain_data(directory_lde1, 0)
#     data_lde2 = obtain_data(directory_lde2, 0)

#     data_mie0 = obtain_data(directory_mie0, 1)
#     data_mie1 = obtain_data(directory_mie1, 1)
#     data_mie2 = obtain_data(directory_mie2, 1)

#     data_greed0 = obtain_data(directory_greed0, 2)
#     data_greed1 = obtain_data(directory_greed1, 2)
#     data_greed2 = obtain_data(directory_greed2, 2)

#     plot_data(main_directory, data_lde0, data_lde1, data_lde2, data_mie0, data_mie1, data_mie2, data_greed0, data_greed1, data_greed2)
#     plt.show()

def obtain_data(directory, label):

    history = np.load('%shistory.npz' % directory)

    learned_classifier = history['learned_classifier']
    mistake_ratio_array = history['mistake_ratio_array']
    entropy_linearised_array = history['entropy_linearised_array']
    entropy_linearised_mean_array = history['entropy_linearised_mean_array']
    entropy_true_mean_array = history['entropy_true_mean_array']
    entropy_opt_array = history['entropy_opt_array']

    return learned_classifier, mistake_ratio_array, entropy_linearised_array, entropy_linearised_mean_array, entropy_true_mean_array, entropy_opt_array, label

def plot_data(directory, *args):

    fig = plt.figure(figsize = (20, 20))

    L = 0.2
    colors = cm.rainbow(np.linspace(0 + L, 1 - L, 5))

    fontsize = 24
    axis_tick_font_size = 14

    ax1 = fig.add_subplot(511)
    ax2 = fig.add_subplot(512)
    ax3 = fig.add_subplot(513)
    ax4 = fig.add_subplot(514)
    ax5 = fig.add_subplot(515)

    for arg in args:

        learned_classifier, mistake_ratio_array, entropy_linearised_array, entropy_linearised_mean_array, entropy_true_mean_array, entropy_opt_array, label = arg

        steps = np.arange(mistake_ratio_array.shape[0]) + 1
        
        color = colors[label[0]]

        ax1.plot(steps, 100 * mistake_ratio_array, c = color, label = label[1])
        ax2.plot(steps, entropy_linearised_array, c = color, label = label[1])
        ax3.plot(steps, entropy_linearised_mean_array, c = color, label = label[1])
        ax4.plot(steps, entropy_true_mean_array, c = color, label = label[1])
        ax5.plot(steps, entropy_opt_array, c = color, label = label[1])

        print(color, label)

    ax1.legend(bbox_to_anchor=(0., 0.8, 1., .05), loc=3,
           ncol=4, borderaxespad=0.)

    plt.subplot(5, 1, 1)
    plt.title('Percentage of Prediction Misses', fontsize = fontsize)
    plt.ylabel('Misses (%)', fontsize = fontsize)
    plt.gca().set_xticklabels( () )

    plt.subplot(5, 1, 2)
    plt.title('Joint Linearised Differential Entropy', fontsize = fontsize)
    plt.ylabel('Entropy (nats)', fontsize = fontsize)
    plt.gca().set_xticklabels( () )

    plt.subplot(5, 1, 3)
    plt.title('Average Marginalised Differential Entropy', fontsize = fontsize)
    plt.ylabel('Entropy (nats)', fontsize = fontsize)
    plt.gca().set_xticklabels( () )

    plt.subplot(5, 1, 4)
    plt.title('Average Marginalised Information Entropy', fontsize = fontsize)
    plt.ylabel('Entropy (nats)', fontsize = fontsize)
    plt.gca().set_xticklabels( () )

    plt.subplot(5, 1, 5)
    plt.gca().get_xaxis().get_major_formatter().set_useOffset(False)
    plt.title('Entropy Metric of Proposed Path', fontsize = fontsize)
    plt.ylabel('Entropy (nats)', fontsize = fontsize)

    
    plt.gca().set_xlabel('Steps', fontsize = fontsize)
    for tick in plt.gca().xaxis.get_major_ticks():
        tick.label.set_fontsize(axis_tick_font_size) 
    for tick in plt.gca().yaxis.get_major_ticks():
        tick.label.set_fontsize(axis_tick_font_size) 



    # Save the plot
    plt.tight_layout()
    plt.savefig('%shistory.png' % directory)

def convert_old_to_new_format(*directories):

    for directory in directories:

        learned_classifier_file = np.load('%slearned_classifier_trial300.npz' % directory)
        learned_classifier = learned_classifier_file['learned_classifier']

        mistake_ratio_array_file = np.load('%smistake_ratio_array_trial300.npz' % directory)
        mistake_ratio_array = mistake_ratio_array_file['mistake_ratio_array']

        entropy_linearised_array_file = np.load('%sentropy_linearised_array_trial300.npz' % directory)
        entropy_linearised_array = entropy_linearised_array_file['entropy_linearised_array']

        entropy_linearised_mean_array_file = np.load('%sentropy_linearised_mean_array_trial300.npz' % directory)
        entropy_linearised_mean_array = entropy_linearised_mean_array_file['entropy_linearised_mean_array']

        entropy_true_mean_array_file = np.load('%sentropy_true_mean_array_trial300.npz' % directory)
        entropy_true_mean_array = entropy_true_mean_array_file['entropy_true_mean_array']

        entropy_opt_array_file = np.load('%sentropy_opt_array_trial300.npz' % directory)
        entropy_opt_array = entropy_opt_array_file['entropy_opt_array']

        np.savez('%shistory.npz' % directory, 
            learned_classifier = learned_classifier,
            mistake_ratio_array = mistake_ratio_array,
            entropy_linearised_array = entropy_linearised_array,
            entropy_linearised_mean_array = entropy_linearised_mean_array,
            entropy_true_mean_array = entropy_true_mean_array,
            entropy_opt_array = entropy_opt_array)

if __name__ == "__main__":
    main()