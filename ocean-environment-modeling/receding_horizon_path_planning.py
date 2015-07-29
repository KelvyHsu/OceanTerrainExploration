"""
Demonstration of simple exploration algorithms using generated data

Author: Kelvin
"""
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib import cm
from computers import gp
import computers.unsupervised.whitening as pre
import sys
import logging
import shutil
import nlopt
import time
import parmap

# Talk about why linearising keeps the squashed probability 
# distributed as a gaussian (yes, the probability itself is a random variable)

plt.ion()

# Define the kernel used for classification
def kerneldef(h, k):
    return h(1e-3, 1e5, 10) * k('gaussian', 
                                [h(1e-3, 1e3, 0.1), h(1e-3, 1e3, 0.1)])

def main():

    """
    Demostration Options
    """
    logging.basicConfig(level = logging.DEBUG)

    # If using parallel functionality, you must call this to set the appropriate
    # logging level
    gp.classifier.set_multiclass_logging_level(logging.DEBUG)

    np.random.seed(50)
    # Feature Generation Parameters and Demonstration Options
    SAVE_OUTPUTS = True # We don't want to make files everywhere for a demo.
    SHOW_RAW_BINARY = True
    test_range_min = -2.5
    test_range_max = +2.5
    test_ranges = (test_range_min, test_range_max)
    n_train = 500
    n_query = 5
    n_dims  = 2   # <- Must be 2 for vis
    n_cores = None # number of cores for multi-class (None -> default: c-1)
    walltime = 300.0
    approxmethod = 'laplace' # 'laplace' or 'pls'
    multimethod = 'OVA' # 'AVA' or 'OVA', ignored for binary problem
    fusemethod = 'EXCLUSION' # 'MODE' or 'EXCLUSION', ignored for binary
    responsename = 'probit' # 'probit' or 'logistic'
    batch_start = False
    entropy_threshold = None

    n_draws = 6
    rows_subplot = 2
    cols_subplot = 3

    assert rows_subplot * cols_subplot >= n_draws

    # Decision boundaries
    db1 = lambda x1, x2: (((x1 - 1)**2 + x2**2/4) * 
            (0.9*(x1 + 1)**2 + x2**2/2) < 1.6) & \
            ((x1 + x2) < 1.5)
    db2 = lambda x1, x2: (((x1 - 1)**2 + x2**2/4) * 
            (0.9*(x1 + 1)**2 + x2**2/2) > 0.3)
    db3 = lambda x1, x2: ((x1 + x2) < 2) & ((x1 + x2) > -2.2)
    db4 = lambda x1, x2: ((x1 - 0.75)**2 + (x2 + 0.8)**2 > 0.3**2)
    db5 = lambda x1, x2: ((x1/2)**2 + x2**2 > 0.3)
    db6 = lambda x1, x2: (((x1)/8)**2 + (x2 + 1.5)**2 > 0.2**2)
    db7 = lambda x1, x2: (((x1)/8)**2 + ((x2 - 1.4)/1.25)**2 > 0.2**2)
    db4a = lambda x1, x2: ((x1 - 1.25)**2 + (x2 - 1.25)**2 > 0.5**2) & ((x1 - 0.75)**2 + (x2 + 1.2)**2 > 0.6**2) & ((x1 + 0.75)**2 + (x2 + 1.2)**2 > 0.3**2) & ((x1 + 1.3)**2 + (x2 - 1.3)**2 > 0.4**2)
    db5a = lambda x1, x2: ((x1/2)**2 + x2**2 > 0.3) & (x1 > 0)
    db5b = lambda x1, x2: ((x1/2)**2 + x2**2 > 0.3) & (x1 < 0) & ((x1 + 0.75)**2 + (x2 - 1.2)**2 > 0.6**2)
    db1a = lambda x1, x2: (((x1 - 1)**2 + x2**2/4) * 
            (0.9*(x1 + 1)**2 + x2**2/2) < 1.6) & \
            ((x1 + x2) < 1.6) | ((x1 + 0.75)**2 + (x2 + 1.2)**2 < 0.6**2)
    db1b = lambda x1, x2: (((x1 - 1)**2 + x2**2/4) * 
            (0.9*(x1 + 1)**2 + x2**2/2) < 1.6) & ((x1/2)**2 + (x2)**2 > 0.4**2) & \
            ((x1 + x2) < 1.5) | ((x1 + 0.75)**2 + (x2 - 1.5)**2 < 0.4**2) | ((x1 + x2) > 2.25) & (x1 < 1.75) & (x2 < 1.75) # | (((x1 + 0.25)/4)**2 + (x2 + 1.5)**2 < 0.32**2) # & (((x1 + 0.25)/4)**2 + (x2 + 1.5)**2 > 0.18**2)
    db1c = lambda x1, x2: (((x1 - 1)**2 + x2**2/4) * 
            (0.9*(x1 + 1)**2 + x2**2/2) < 1.6) & ((x1/2)**2 + (x2)**2 > 0.4**2) & \
            ((x1 + x2) < 1.5) | ((x1 + 0.75)**2 + (x2 - 1.5)**2 < 0.4**2) | ((x1 + x2) > 2.25) & (x1 < 1.75) & (x2 < 1.75) | (((x1 + 0.25)/4)**2 + (x2 + 1.75)**2 < 0.32**2) & (((x1 + 0.25)/4)**2 + (x2 + 1.75)**2 > 0.18**2)
    db8 = lambda x1, x2: (np.sin(2*x1 + 3*x2) > 0) | (((x1 - 1)**2 + x2**2/4) * 
            (0.9*(x1 + 1)**2 + x2**2/2) < 1.4) & \
            ((x1 + x2) < 1.5) | (x1 < -1.9) | (x1 > +1.9) | (x2 < -1.9) | (x2 > +1.9) | ((x1 + 0.75)**2 + (x2 - 1.5)**2 < 0.3**2)
    # db9 = lambda x1, x2: ((x1)**2 + (x2)**2 < 0.3**2) | ((x1)**2 + (x2)**2 > 0.5**2) |
    decision_boundary  = [db5b, db1c, db4a]

    """
    Data Generation
    """

    # # # Training Points
    # shrink = 0.8
    # test_range_min *= shrink
    # test_range_max *= shrink
    # X1 = np.random.normal(loc = np.array([test_range_min, test_range_min]), scale = 0.9*np.ones(n_dims), size = (int(n_train/8), n_dims))
    # X2 = np.random.normal(loc = np.array([test_range_min, test_range_max]), scale = 0.9*np.ones(n_dims), size = (int(n_train/8), n_dims))
    # X3 = np.random.normal(loc = np.array([test_range_max, test_range_min]), scale = 0.9*np.ones(n_dims), size = (int(n_train/8), n_dims))
    # X4 = np.random.normal(loc = np.array([test_range_max, test_range_max]), scale = 0.9*np.ones(n_dims), size = (int(n_train/8), n_dims))
    # X5 = np.random.normal(loc = np.array([0, test_range_min]), scale = 0.9*np.ones(n_dims), size = (int(n_train/8), n_dims))
    # X6 = np.random.normal(loc = np.array([test_range_min, 0]), scale = 0.9*np.ones(n_dims), size = (int(n_train/8), n_dims))
    # X7 = np.random.normal(loc = np.array([test_range_max, 0]), scale = 0.9*np.ones(n_dims), size = (int(n_train/8), n_dims))
    # X8 = np.random.normal(loc = np.array([0, test_range_max]), scale = 0.9*np.ones(n_dims), size = (int(n_train/8), n_dims))
    # test_range_min /= shrink
    # test_range_max /= shrink

    # X = np.concatenate((X1, X2, X3, X4, X5, X6, X7, X8), axis = 0)

    X = np.random.uniform(test_range_min, test_range_max, 
        size = (n_train, n_dims))

    # X_s = np.array([[0.0, 0.0], [-0.2, 0.3], [-0.1, -0.1], [0.05, 0.25], [-1.1, 0.0], [-0.5, 0.0], [-0.4, -0.7], [-0.1, -0.1], [test_range_min, test_range_min], [test_range_min, test_range_max], [test_range_max, test_range_max], [test_range_max, test_range_min]])
    # X_f = np.array([[1.4, 1.6], [1.8, 1.2], [-1.24, 1.72], [-1.56, -1.9], [-1.9, 1.0], [-0.5, -1.2], [-1.4, -1.9], [0.4, -1.2], [test_range_min, test_range_max], [test_range_max, test_range_max], [test_range_max, test_range_min], [test_range_min, test_range_min]])
    # X = generate_line_paths(X_s, X_f)
    x1 = X[:, 0]
    x2 = X[:, 1]
    
    # Query Points
    Xq = np.random.uniform(test_range_min, test_range_max, 
        size = (n_query, n_dims))
    xq1 = Xq[:, 0]
    xq2 = Xq[:, 1]

    # Training Labels
    y = gp.classifier.utils.make_decision(X, decision_boundary)
    y_unique = np.unique(y)

    if y_unique.shape[0] == 2:
        mycmap = cm.get_cmap(name = 'bone', lut = None)
        mycmap2 = cm.get_cmap(name = 'BrBG', lut = None)
    else:
        mycmap = cm.get_cmap(name = 'gist_rainbow', lut = None)
        mycmap2 = cm.get_cmap(name = 'gist_rainbow', lut = None)
    """
    Classifier Training
    """

    # Training
    fig = plt.figure()
    gp.classifier.utils.visualise_decision_boundary(
        test_range_min, test_range_max, decision_boundary)
    
    plt.scatter(x1, x2, c = y, marker = 'x', cmap = mycmap)
    plt.title('Training Labels')
    plt.xlabel('x1')
    plt.ylabel('x2')
    cbar = plt.colorbar()
    cbar.set_ticks(y_unique)
    cbar.set_ticklabels(y_unique)
    plt.xlim((test_range_min, test_range_max))
    plt.ylim((test_range_min, test_range_max))
    plt.gca().patch.set_facecolor('gray')
    print('Plotted Training Set')

    plt.show()

    # Training
    print('===Begin Classifier Training===')
    optimiser_config = gp.OptConfig()
    optimiser_config.sigma = gp.auto_range(kerneldef)
    optimiser_config.walltime = walltime

    # User can choose to batch start each binary classifier with different
    # initial hyperparameters for faster training
    if batch_start:
        if y_unique.shape[0] == 2:
            initial_hyperparams = [100, 0.1, 0.1]
        elif multimethod == 'OVA':
            initial_hyperparams = [  [356.468, 0.762, 0.530], \
                                     [356.556, 0.836, 0.763], \
                                     [472.006, 1.648, 1.550], \
                                     [239.720, 1.307, 0.721] ]
        elif multimethod == 'AVA':
            initial_hyperparams = [ [14.9670, 0.547, 0.402],  \
                                    [251.979, 1.583, 1.318], \
                                    [420.376, 1.452, 0.750], \
                                    [780.641, 1.397, 1.682], \
                                    [490.353, 2.299, 1.526], \
                                    [73.999, 1.584, 0.954]]
        else:
            raise ValueError
        batch_config = gp.batch_start(optimiser_config, initial_hyperparams)
    else:
        batch_config = optimiser_config

    # Obtain the response function
    responsefunction = gp.classifier.responses.get(responsename)

    # Train the classifier!
    learned_classifier = gp.classifier.learn(X, y, kerneldef,
        responsefunction, batch_config, 
        multimethod = multimethod, approxmethod = approxmethod,
        train = True, ftol = 1e-10, processes = n_cores)

    # Print learned kernels
    print_function = gp.describer(kerneldef)
    gp.classifier.utils.print_learned_kernels(print_function, 
                                            learned_classifier, y_unique)

    # Print the matrix of learned classifier hyperparameters
    logging.info('Matrix of learned hyperparameters')
    gp.classifier.utils.print_hyperparam_matrix(learned_classifier)
    
    """
    Classifier Prediction
    """

    # Obtain the prediction function
    prediction_function = lambda Xq: gp.classifier.predict(Xq, 
                            learned_classifier,
                            fusemethod = fusemethod, processes = n_cores)
    # Prediction
    yq_prob = prediction_function(Xq)
    yq_pred = gp.classifier.classify(yq_prob, y)
    yq_entropy = gp.classifier.entropy(yq_prob)

    logging.info('Caching Predictor...')
    predictors = gp.classifier.query(learned_classifier, Xq)
    logging.info('Computing Expectance...')
    yq_exp_list = gp.classifier.expectance(learned_classifier, predictors)
    logging.info('Computing Covariance...')
    yq_cov_list = gp.classifier.covariance(learned_classifier, predictors)
    logging.info('Drawing from GP...')
    yq_draws = gp.classifier.draws(n_draws, yq_exp_list, yq_cov_list, 
        learned_classifier)

    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
                        THE GAP BETWEEN ANALYSIS AND PLOTS
    """""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""







    """
    Classifier Prediction Results (Plots)
    """

    logging.info('Plotting... please wait')

    """
    Plot: Training Set
    """

    # Training
    fig = plt.figure(figsize = (15, 15))
    gp.classifier.utils.visualise_decision_boundary(
        test_range_min, test_range_max, decision_boundary)
    
    plt.scatter(x1, x2, c = y, marker = 'x', cmap = mycmap)
    plt.title('Training Labels')
    plt.xlabel('x1')
    plt.ylabel('x2')
    cbar = plt.colorbar()
    cbar.set_ticks(y_unique)
    cbar.set_ticklabels(y_unique)
    plt.xlim((test_range_min, test_range_max))
    plt.ylim((test_range_min, test_range_max))
    plt.gca().patch.set_facecolor('gray')
    logging.info('Plotted Training Set')

    """
    Plot: Query Computations
    """

    Xq_plt = gp.classifier.utils.query_map(test_ranges)

    logging.info('Caching Predictor...')
    predictor_plt = gp.classifier.query(learned_classifier, Xq_plt)
    logging.info('Computing Expectance...')
    expectance_latent_plt = gp.classifier.expectance(learned_classifier, 
        predictor_plt)
    logging.info('Computing Variance...')
    variance_latent_plt = gp.classifier.variance(learned_classifier, 
        predictor_plt)
    logging.info('Computing Prediction Probabilities...')
    yq_prob_plt = gp.classifier.predict_from_latent(expectance_latent_plt, 
        variance_latent_plt, learned_classifier, fusemethod = fusemethod)
    logging.info('Computing Prediction Entropy...')
    yq_entropy_plt = gp.classifier.entropy(yq_prob_plt)
    logging.info('Computing Prediction...')
    yq_pred_plt = gp.classifier.classify(yq_prob_plt, y)
    logging.info('Computing Linearised Entropy...')
    entropy_linearised_plt = gp.classifier.linearised_entropy(
        expectance_latent_plt, variance_latent_plt, learned_classifier)

    logging.info('Computing Separated Linearised Entropy...')
    if isinstance(learned_classifier, list):
        args = [(expectance_latent_plt[i], variance_latent_plt[i], 
            learned_classifier[i]) for i in range(len(learned_classifier))]
        entropy_linearised_separated_plt = \
            parmap.starmap(gp.classifier.linearised_entropy, args)

    # logging.info('Fusing Linearised Entropy...')
    # entropy_linearised_plt = \
    #     np.array(entropy_linearised_separated_plt).max(axis = 0)

    if isinstance(learned_classifier, list):

        """
        Plot: Latent Function Expectance
        """

        for i in range(len(expectance_latent_plt)):
            fig = plt.figure(figsize = (15, 15))
            gp.classifier.utils.visualise_map(expectance_latent_plt[i], test_ranges, 
                levels = [0.0], vmin = -np.max(np.abs(expectance_latent_plt[i])), 
                vmax = np.max(np.abs(expectance_latent_plt[i])), cmap = cm.coolwarm)
            plt.title('Latent Funtion Expectance %s' 
                % gp.classifier.utils.binary_classifier_name(learned_classifier[i], 
                    y_unique))
            plt.xlabel('x1')
            plt.ylabel('x2')
            plt.colorbar()
            plt.scatter(x1, x2, c = y, marker = 'x', cmap = mycmap)
            plt.xlim((test_range_min, test_range_max))
            plt.ylim((test_range_min, test_range_max))
            logging.info('Plotted Latent Function Expectance on Training Set')

        """
        Plot: Latent Function Variance
        """

        for i in range(len(variance_latent_plt)):
            fig = plt.figure(figsize = (15, 15))
            gp.classifier.utils.visualise_map(variance_latent_plt[i], test_ranges, 
                cmap = cm.coolwarm)
            plt.title('Latent Funtion Variance %s' 
                % gp.classifier.utils.binary_classifier_name(learned_classifier[i], 
                    y_unique))
            plt.xlabel('x1')
            plt.ylabel('x2')
            plt.colorbar()
            plt.scatter(x1, x2, c = y, marker = 'x', cmap = mycmap)
            plt.xlim((test_range_min, test_range_max))
            plt.ylim((test_range_min, test_range_max))
            logging.info('Plotted Latent Function Variance on Training Set')

        """
        Plot: Prediction Probabilities
        """

        for i in range(len(yq_prob_plt)):
            fig = plt.figure(figsize = (15, 15))
            gp.classifier.utils.visualise_map(yq_prob_plt[i], test_ranges, 
                levels = [0.5], cmap = cm.coolwarm)
            plt.title('Prediction Probabilities (Class %d)' % y_unique[i])
            plt.xlabel('x1')
            plt.ylabel('x2')
            plt.colorbar()
            plt.scatter(x1, x2, c = y, marker = 'x', cmap = mycmap)
            plt.xlim((test_range_min, test_range_max))
            plt.ylim((test_range_min, test_range_max))
            logging.info('Plotted Prediction Probabilities on Training Set')

        """
        Plot: Individual Linearised Entropy
        """

        for i in range(len(entropy_linearised_separated_plt)):
            fig = plt.figure(figsize = (15, 15))
            gp.classifier.utils.visualise_map(entropy_linearised_separated_plt[i], 
                test_ranges, cmap = cm.coolwarm)
            plt.title('Individual Linearised Entropy %s' 
                % gp.classifier.utils.binary_classifier_name(learned_classifier[i], 
                    y_unique))
            plt.xlabel('x1')
            plt.ylabel('x2')
            plt.colorbar()
            plt.scatter(x1, x2, c = y, marker = 'x', cmap = mycmap)
            plt.xlim((test_range_min, test_range_max))
            plt.ylim((test_range_min, test_range_max))
            logging.info('Plotted Individual Linearised Entropy on Training Set')

    """
    Plot: Prediction Labels
    """

    # Query (Prediction Map)
    fig = plt.figure(figsize = (15, 15))
    gp.classifier.utils.visualise_map(yq_pred_plt, test_ranges, 
        boundaries = True, cmap = mycmap)
    plt.title('Prediction')
    plt.xlabel('x1')
    plt.ylabel('x2')
    cbar = plt.colorbar()
    cbar.set_ticks(y_unique)
    cbar.set_ticklabels(y_unique)
    logging.info('Plotted Prediction Labels')

    """
    Plot: Prediction Entropy onto Training Set
    """

    # Query (Prediction Entropy) and Training Set
    fig = plt.figure(figsize = (15, 15))
    gp.classifier.utils.visualise_map(yq_entropy_plt, test_ranges, 
        threshold = entropy_threshold, cmap = cm.coolwarm)
    plt.title('Prediction Entropy and Training Set')
    plt.xlabel('x1')
    plt.ylabel('x2')
    plt.colorbar()
    plt.scatter(x1, x2, c = y, marker = 'x', cmap = mycmap)
    plt.xlim((test_range_min, test_range_max))
    plt.ylim((test_range_min, test_range_max))
    logging.info('Plotted Prediction Entropy on Training Set')

    """
    Plot: Linearised Prediction Entropy onto Training Set
    """

    # Query (Linearised Entropy) and Training Set
    fig = plt.figure(figsize = (15, 15))
    gp.classifier.utils.visualise_map(entropy_linearised_plt, test_ranges, 
        threshold = entropy_threshold, cmap = cm.coolwarm)
    plt.title('Linearised Prediction Entropy and Training Set')
    plt.xlabel('x1')
    plt.ylabel('x2')
    plt.colorbar()
    plt.scatter(x1, x2, c = y, marker = 'x', cmap = mycmap)
    plt.xlim((test_range_min, test_range_max))
    plt.ylim((test_range_min, test_range_max))
    logging.info('Plotted Linearised Prediction Entropy on Training Set')

    """
    Plot: Sample Query Predictions
    """  

    # Visualise Predictions
    fig = plt.figure(figsize = (15, 15))
    gp.classifier.utils.visualise_decision_boundary(
        test_range_min, test_range_max, decision_boundary)
    plt.scatter(xq1, xq2, c = yq_pred, marker = 'x', cmap = mycmap)
    plt.title('Predicted Query Labels')
    plt.xlabel('x1')
    plt.ylabel('x2')
    cbar = plt.colorbar()
    cbar.set_ticks(y_unique)
    cbar.set_ticklabels(y_unique)
    plt.xlim((test_range_min, test_range_max))
    plt.ylim((test_range_min, test_range_max))
    plt.gca().patch.set_facecolor('gray')
    logging.info('Plotted Sample Query Labels')

    """
    Plot: Sample Query Draws
    """  

    # Visualise Predictions
    fig = plt.figure(figsize = (19.2, 10.8))
    for i in range(n_draws):
        plt.subplot(rows_subplot, cols_subplot, i + 1)
        gp.classifier.utils.visualise_decision_boundary(
            test_range_min, test_range_max, decision_boundary)
        plt.scatter(xq1, xq2, c = yq_draws[i], marker = 'x', cmap = mycmap)
        plt.title('Query Label Draws')
        plt.xlabel('x1')
        plt.ylabel('x2')
        cbar = plt.colorbar()
        cbar.set_ticks(y_unique)
        cbar.set_ticklabels(y_unique)
        plt.xlim((test_range_min, test_range_max))
        plt.ylim((test_range_min, test_range_max))
        plt.gca().patch.set_facecolor('gray')
        logging.info('Plotted Sample Query Draws')

    """
    Save Outputs
    """  

    # Save all the figures
    if SAVE_OUTPUTS:
        save_directory = "response_%s_approxmethod_%s" \
        "_training_%d_query_%d_walltime_%d" \
        "_method_%s_fusemethod_%s/" \
            % ( responsename, approxmethod, 
                n_train, n_query, walltime, 
                multimethod, fusemethod)
        full_directory = gp.classifier.utils.create_directories(
            save_directory, home_directory = 'Figures/', append_time = True)
        gp.classifier.utils.save_all_figures(full_directory)
        shutil.copy2('./receding_horizon_path_planning.py', full_directory)


    logging.info('Modeling Done')
    return
    """
    Path Planning
    """

    """ Setup Path Planning """
    xq_now = np.array([[0., 0.]])
    horizon = (test_range_max - test_range_min)/2
    n_steps = 20

    theta_bound = np.deg2rad(60)
    theta_add_init = np.zeros(n_steps)
    theta_add_init[0] = np.deg2rad(270)
    theta_add_low = -theta_bound * np.ones(n_steps)
    theta_add_high = theta_bound * np.ones(n_steps)
    theta_add_low[0] = 0.0
    theta_add_high[0] = 2 * np.pi
    r = horizon/n_steps
    choice_walltime = 3000.0
    xtol_rel = 1e-2
    ftol_rel = 1e-6

    k_step = 1

    """ Initialise Values """

    # The observed data till now
    X_now = X.copy()
    y_now = y.copy()

    # Observe the current location
    yq_now = gp.classifier.utils.make_decision(xq_now[[-1]], 
        decision_boundary)

    # Add the observed data to the training set
    X_now = np.concatenate((X_now, xq_now[[-1]]), axis = 0)
    y_now = np.append(y_now, yq_now)

    # Add the new location to the array of travelled coordinates
    xq1_nows = xq_now[:, 0]
    xq2_nows = xq_now[:, 1]
    yq_nows = yq_now.copy()

    # Plot the current situation
    fig1 = plt.figure(figsize = (15, 15))
    fig2 = plt.figure(figsize = (15, 15))
    fig3 = plt.figure(figsize = (15, 15))

    # Start exploring
    i_trials = 0
    while i_trials < 2001:

        """ Path Planning """

        # Propose a place to observe
        xq_abs_opt, theta_add_opt, entropy_opt = \
            go_optimised_path(theta_add_init, xq_now[-1], r, 
                learned_classifier, test_ranges,
                theta_add_low = theta_add_low, theta_add_high = theta_add_high, 
                walltime = choice_walltime, xtol_rel = xtol_rel, 
                ftol_rel = ftol_rel)
        logging.info('Optimal Joint Entropy: %.5f' % entropy_opt)

        xq_now = xq_abs_opt[:k_step]

        theta_add_init = initiate_with_continuity(theta_add_opt, 
            k_step = k_step)
        np.clip(theta_add_init, theta_add_low + 1e-4, theta_add_high - 1e-4, 
            out = theta_add_init)

        # Observe the current location
        yq_now = gp.classifier.utils.make_decision(xq_now, 
            decision_boundary)

        # Add the observed data to the training set
        X_now = np.concatenate((X_now, xq_now), axis = 0)
        y_now = np.append(y_now, yq_now)

        # Add the new location to the array of travelled coordinates
        xq1_nows = np.append(xq1_nows, xq_now[:, 0])
        xq2_nows = np.append(xq2_nows, xq_now[:, 1])
        yq_nows = np.append(yq_nows, yq_now)

        # Update that into the model
        logging.info('Learning Classifier...')
        batch_config = \
            gp.classifier.batch_start(optimiser_config, learned_classifier)
        try:
            learned_classifier = gp.classifier.learn(X_now, y_now, kerneldef,
                responsefunction, batch_config, 
                multimethod = multimethod, approxmethod = approxmethod,
                train = True, ftol = 1e-4, processes = n_cores)
        except:
            learned_classifier = gp.classifier.learn(X_now, y_now, kerneldef,
                responsefunction, batch_config, 
                multimethod = multimethod, approxmethod = approxmethod,
                train = False, ftol = 1e-4, processes = n_cores)      

        # This is the finite horizon optimal route
        xq1_proposed = xq_abs_opt[:, 0][k_step:]
        xq2_proposed = xq_abs_opt[:, 1][k_step:]
        yq_proposed = gp.classifier.classify(gp.classifier.predict(xq_abs_opt, 
            learned_classifier), y_unique)[k_step:]

        """ Computing Analysis Maps """

        # Compute Linearised and True Entropy for plotting
        logging.info('Plot: Caching Predictor...')
        predictor_plt = gp.classifier.query(learned_classifier, Xq_plt)
        logging.info('Plot: Computing Expectance...')
        expectance_latent_plt = \
            gp.classifier.expectance(learned_classifier, predictor_plt)
        logging.info('Plot: Computing Variance...')
        variance_latent_plt = \
            gp.classifier.variance(learned_classifier, predictor_plt)
        logging.info('Plot: Computing Linearised Entropy...')
        entropy_linearised_plt = gp.classifier.linearised_entropy(
            expectance_latent_plt, variance_latent_plt, learned_classifier)
        logging.info('Plot: Computing Prediction Probabilities...')
        probabilities_plt = gp.classifier.predict_from_latent(
            expectance_latent_plt, variance_latent_plt, learned_classifier, 
            fusemethod = fusemethod)
        logging.info('Plot: Computing True Entropy...')
        entropy_plt = gp.classifier.entropy(probabilities_plt)
        logging.info('Plot: Computing Class Predicitons')
        class_plt = gp.classifier.classify(probabilities_plt, y_unique)

        # Find the bounds of the entropy predictions
        vmin1 = entropy_linearised_plt.min()
        vmax1 = entropy_linearised_plt.max()
        vmin2 = entropy_plt.min()
        vmax2 = entropy_plt.max()

        """ Linearised Entropy Map """

        # Prepare Figure 1
        plt.figure(fig1.number)
        plt.clf()
        plt.title('Exploration track and linearised entropy [horizon = %.2f]' 
            % horizon)
        plt.xlabel('x1')
        plt.ylabel('x2')
        plt.xlim((test_range_min, test_range_max))
        plt.ylim((test_range_min, test_range_max))

        # Plot linearised entropy
        gp.classifier.utils.visualise_map(entropy_linearised_plt, test_ranges, 
            cmap = cm.coolwarm, vmin = vmin1, vmax = vmax1)
        plt.colorbar()

        # Plot training set on top
        plt.scatter(x1, x2, c = y, s = 40, marker = 'x', cmap = mycmap)

        # Plot the path on top
        plt.scatter(xq1_nows, xq2_nows, c = yq_nows, s = 60, 
            facecolors = 'none',
            vmin = y_unique[0], vmax = y_unique[-1], cmap = mycmap)
        plt.scatter(xq_now[:, 0], xq_now[:, 1], c = yq_now, s = 120, 
            vmin = y_unique[0], vmax = y_unique[-1], 
            cmap = mycmap)

        # Plot the proposed path
        plt.scatter(xq1_proposed, xq2_proposed, c = yq_proposed, 
            s = 60, marker = 'D', 
            vmin = y_unique[0], vmax = y_unique[-1], cmap = mycmap)

        # Plot the horizon
        gp.classifier.utils.plot_circle(xq_now[-1], horizon, c = 'k', 
            marker = '.')

        # Save the plot
        plt.gca().set_aspect('equal', adjustable = 'box')
        plt.savefig('%sentropy_linearised_step%d.png' 
            % (full_directory, i_trials + 1))

        """ True Entropy Map """

        # Prepare Figure 2
        plt.figure(fig2.number)
        plt.clf()
        plt.title('Exploration track and true entropy [horizon = %.2f]' 
            % horizon)
        plt.xlabel('x1')
        plt.ylabel('x2')
        plt.xlim((test_range_min, test_range_max))
        plt.ylim((test_range_min, test_range_max))

        # Plot true entropy
        gp.classifier.utils.visualise_map(entropy_plt, test_ranges, 
            cmap = cm.coolwarm, vmin = vmin2, vmax = vmax2)
        plt.colorbar()

        # Plot training set on top
        plt.scatter(x1, x2, c = y, s = 40, marker = 'x', cmap = mycmap)

        # Plot the path on top
        plt.scatter(xq1_nows, xq2_nows, c = yq_nows, s = 60, 
            facecolors = 'none',
            vmin = y_unique[0], vmax = y_unique[-1], cmap = mycmap)
        plt.scatter(xq_now[:, 0], xq_now[:, 1], c = yq_now, s = 120, 
            vmin = y_unique[0], vmax = y_unique[-1], 
            cmap = mycmap)

        # Plot the proposed path
        plt.scatter(xq1_proposed, xq2_proposed, c = yq_proposed, 
            s = 60, marker = 'D', 
            vmin = y_unique[0], vmax = y_unique[-1], cmap = mycmap)

        # Plot the horizon
        gp.classifier.utils.plot_circle(xq_now[-1], horizon, c = 'k', 
            marker = '.')

        # Save the plot
        plt.gca().set_aspect('equal', adjustable = 'box')
        plt.savefig('%sentropy_true_step%d.png' 
            % (full_directory, i_trials + 1))

        """ Class Prediction Map """

        # Prepare Figure 3
        plt.figure(fig3.number)
        plt.clf()
        plt.title('Exploration track and class predictions [horizon = %.2f]' 
            % horizon)
        plt.xlabel('x1')
        plt.ylabel('x2')
        plt.xlim((test_range_min, test_range_max))
        plt.ylim((test_range_min, test_range_max))

        # Plot class predictions
        gp.classifier.utils.visualise_map(class_plt, test_ranges, 
            boundaries = True, cmap = mycmap2)
        try:
            cbar = plt.colorbar()
            cbar.set_ticks(y_unique)
            cbar.set_ticklabels(y_unique)
        except IndexError:
            pass


        # Plot training set on top
        plt.scatter(x1, x2, c = y, s = 40, marker = 'v', cmap = mycmap)

        # Plot the path on top
        plt.scatter(xq1_nows, xq2_nows, c = yq_nows, s = 60, marker = 'o', 
            vmin = y_unique[0], vmax = y_unique[-1], cmap = mycmap)
        plt.scatter(xq_now[:, 0], xq_now[:, 1], c = yq_now, s = 120, 
            vmin = y_unique[0], vmax = y_unique[-1], 
            cmap = mycmap)

        # Plot the proposed path
        plt.scatter(xq1_proposed, xq2_proposed, c = yq_proposed, 
            s = 60, marker = 'D', 
            vmin = y_unique[0], vmax = y_unique[-1], cmap = mycmap)

        # Plot the horizon
        gp.classifier.utils.plot_circle(xq_now[-1], horizon, c = 'k', 
            marker = '.')

        # Save the plot
        plt.gca().set_aspect('equal', adjustable = 'box')
        plt.savefig('%sclass_prediction_step%d.png' 
            % (full_directory, i_trials + 1))

        # Move on to the next step
        i_trials += 1

        # Save the learned classifier
        if i_trials % 50 == 0:
            np.savez('%slearned_classifier_trial%d.npz'
                % (full_directory, i_trials), 
                learned_classifier = learned_classifier)


    # When finished, save the learned classifier
    np.savez('%slearned_classifier_final.npz' % full_directory, 
        learned_classifier = learned_classifier)

    # Show everything!
    plt.show()

def initiate_with_continuity(theta_add_opt, k_step = 1):

    theta_add_next = np.zeros(theta_add_opt.shape)

    theta_add_next[0] = theta_add_opt[:(k_step + 1)].sum() % (2 * np.pi)
    theta_add_next[1:-k_step] = theta_add_opt[(k_step + 1):]

    return theta_add_next

def boundary_map(Xq): 

    test_range_min = -2.0
    test_range_max = +2.0
    return True if  np.any(Xq[:, 0] < test_range_min) | \
                    np.any(Xq[:, 0] > test_range_max) | \
                    np.any(Xq[:, 1] < test_range_min) | \
                    np.any(Xq[:, 1] > test_range_max)   \
                else False


def forward_path_model(theta_add, r, x):

    theta = np.cumsum(theta_add)

    x1_add = r * np.cos(theta)
    x2_add = r * np.sin(theta)

    x1_rel = np.cumsum(x1_add)
    x2_rel = np.cumsum(x2_add)

    # x_rel = np.concatenate((x1_rel[:, np.newaxis], x2_rel[:, np.newaxis]), axis = 1)
    x_rel = np.array([x1_rel, x2_rel]).T

    Xq = x + x_rel
    return Xq

def path_entropy_model(theta_add, r, x, memory):

    Xq = forward_path_model(theta_add, r, x)

    # if boundary_map(Xq):
    #     return -1e-8

    try:

        start_time = time.clock()
        # Method 1
        logging.info('Computing linearised entropy...')
        predictors = gp.classifier.query(memory, Xq)
        yq_exp = gp.classifier.expectance(memory, predictors)
        yq_cov = gp.classifier.covariance(memory, predictors)
        entropy = gp.classifier.linearised_entropy(yq_exp, yq_cov, memory)
        logging.debug('Linearised Entropy Computational Time : %.8f' % (time.clock() - start_time))

        # # Method 2
        # entropy = gp.classifier.entropy(gp.classifier.predict(Xq, memory)).sum()

        # start_time = time.clock()
        # # Method 3
        # logging.info('Computing joint entropy...')
        # predictors = gp.classifier.query(memory, Xq)
        # yq_exp = gp.classifier.expectance(memory, predictors)
        # yq_cov = gp.classifier.covariance(memory, predictors)

        # try:
        #     path_entropy_model.S == None
        # except AttributeError:
        #     logging.info('Initiating seed draw...')
        #     nq = np.array(yq_exp).shape[-1]
        #     path_entropy_model.S = np.random.normal(0., 1., (nq, 2500))

        # entropy = gp.classifier.joint_entropy(yq_exp, yq_cov, memory, 
        #     S = path_entropy_model.S, n_draws = 2500)
        # logging.debug('Sampled Entropy Computational Time : %.8f' % (time.clock() - start_time))

    except:
        # logging.warning('Failed to compute linearised entropy')
        entropy = -1e8

    logging.debug('theta_add: {0} | entropy: {1}'.format(
        theta_add, entropy))
    return entropy

def path_bounds_model(theta_add, r, x, ranges):

    Xq = forward_path_model(theta_add, r, x)

    c = np.max(np.abs(Xq)) - ranges[1]
    print(c)
    # Assume ranges is symmetric (a square)
    return c

def go_optimised_path(theta_add_init, x, r, memory, ranges,
    theta_add_low = None, theta_add_high = None, walltime = None, 
    xtol_rel = 1e-2, ftol_rel = 1e-2, globalopt = False):

    ##### OPTIMISATION #####
    try:
        def objective(theta_add, grad):
            return path_entropy_model(theta_add, r, x, memory)

        def constraint(theta_add, grad):
            return path_bounds_model(theta_add, r, x, ranges)

        n_params = theta_add_init.shape[0]

        if globalopt:

            opt = nlopt.opt(nlopt.G_MLSL_LDS, n_params)
            local_opt = nlopt.opt(nlopt.LN_COBYLA , n_params)
            opt.set_local_optimizer(local_opt)

        else:

            opt = nlopt.opt(nlopt.LN_COBYLA , n_params)


        opt.set_lower_bounds(theta_add_low)
        opt.set_upper_bounds(theta_add_high)
        opt.set_maxtime(walltime)

        if xtol_rel:
            opt.set_xtol_rel(xtol_rel)

        if ftol_rel:
            opt.set_ftol_rel(ftol_rel)
        

        opt.set_max_objective(objective)
        opt.add_inequality_constraint(constraint, 1e-2)

        theta_add_opt = opt.optimize(theta_add_init)

        entropy_opt = opt.last_optimum_value()

    except Exception as e:

        theta_add_opt = initiate_with_continuity(theta_add_init)
        entropy_opt = np.nan
        logging.warning('Problem with optimisation. Continuing planned route.')
        logging.warning(type(e))
        logging.warning(e)
        logging.debug('Initial parameters: {0}'.format(theta_add_init))

    ##### PATH COMPUTATION #####
    x_abs_opt = forward_path_model(theta_add_opt, r, x)

    return x_abs_opt, theta_add_opt, entropy_opt

def generate_line_path(x_s, x_f, n_points = 10):
    p = x_f - x_s
    r = np.linspace(0, 1, num = n_points)
    return np.outer(r, p) + x_s

def generate_line_paths(X_s, X_f, n_points = 10):

    assert X_s.shape == X_f.shape

    if hasattr(n_points, '__iter__'):

        assert n_points.shape[0] == X_s.shape[0]
        X = np.array([generate_line_path(X_s[i], X_f[i], n_points[i]) for i in range(X_s.shape[0])])
        return X.reshape(X.shape[0] * X.shape[1], X.shape[2])

    else:

        X = np.array([generate_line_path(X_s[i], X_f[i], n_points) for i in range(X_s.shape[0])])
        return X.reshape(X.shape[0] * X.shape[1], X.shape[2])

if __name__ == "__main__":
    main()