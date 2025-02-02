"""
Informative Seafloor Exploration
"""
import numpy as np
import nlopt
from computers import gp
import logging
import time
from scipy.spatial.distance import cdist

def optimal_difference_path(theta_stack_init, r, x, memory, feature_fn, white_params,
    Fs, Fw, y, inference_learn, turn_limit = np.deg2rad(30), bound = 100,
    theta_stack_low = None, theta_stack_high = None,
    walltime = None, xtol_rel = 0, ftol_rel = 0, ctol = 1e-6):

    def objective(theta_stack, grad):
        return difference_acquisition(theta_stack, r, x, memory, feature_fn, white_params, Fs, Fw, y, inference_learn)

    # Define the path constraint
    def constraint(result, theta_stack, grad):
        result = path_bounds_model(theta_stack, r, x, feature_fn.Xq_ref, bound)

    # Obtain the number of parameters involvevd
    n_params = theta_stack_init.shape[0]

    # Prepare for global or local optimisation according to specification
    opt = nlopt.opt(nlopt.LN_COBYLA , n_params)

    # Set lower and upper bound
    if theta_stack_low is not None:
        theta_stack_low[0] = theta_stack_init[0] - turn_limit
        opt.set_lower_bounds(theta_stack_low)
    if theta_stack_high is not None:
        theta_stack_high[0] = theta_stack_init[0] + turn_limit
        opt.set_upper_bounds(theta_stack_high)

    # Set tolerances
    if xtol_rel > 0:
        opt.set_xtol_rel(xtol_rel)
    if ftol_rel > 0:
        opt.set_ftol_rel(ftol_rel)
    
    # Set maximum optimisation time
    opt.set_maxtime(walltime)

    # Set the objective and constraint and optimise!
    opt.set_max_objective(objective)
    opt.add_inequality_mconstraint(constraint, ctol * np.ones(n_params))
    theta_stack_opt = opt.optimize(theta_stack_init)
    entropy_opt = opt.last_optimum_value()

    # Compute optimal path
    x_path_opt = forward_path_model(theta_stack_opt, r, x)

    # Replace the optimal coordinates with the closest query locations
    x_path_opt = feature_fn.closest_locations(x_path_opt)

    # Approximate the corresponding path angles
    theta_stack_opt = backward_path_model(x_path_opt, x)

    # Return path coordinates, path angles, and path entropy
    return x_path_opt, theta_stack_opt, entropy_opt

def difference_acquisition(theta_stack, r, x, memory, feature_fn, white_params, Fs, Fw, y, inference_learn):

    Xq = forward_path_model(theta_stack, r, x)
    Fq = feature_fn.extract(Xq)
    Fqw = feature_fn.whiten(Fq, white_params)
    yq = gp.classifier.predict(Fqw, memory)

    logging.info('Computing difference average marginalised prediction information entropy...')
    start_time = time.clock()

    memory_new = inference_learn(np.concatenate((Fw, Fqw), axis = 0), np.append(y, yq))

    Fsw = feature_fn.whiten(Fs, white_params)

    predictors_s = gp.classifier.query(memory, Fsw)
    ys_exp = gp.classifier.expectance(memory, predictors_s)
    ys_cov = gp.classifier.covariance(memory, predictors_s)
    entropy_s_before = average_marginalised_prediction_information_entropy(ys_exp, ys_cov, memory)

    predictors_s = gp.classifier.query(memory_new, Fsw)
    ys_exp = gp.classifier.expectance(memory_new, predictors_s)
    ys_cov = gp.classifier.covariance(memory_new, predictors_s)
    entropy_s_after = average_marginalised_prediction_information_entropy(ys_exp, ys_cov, memory_new)

    entropy = entropy_s_before - entropy_s_after

    logging.debug('Difference average marginalised prediction information entropy computational time: %.8f' % 
        (time.clock() - start_time))
    logging.debug('Angles (deg): {0} | Entropy: {1}'.format(
        np.rad2deg(theta_stack), entropy))

    return entropy

def optimal_path(theta_stack_init, r, x, memory, feature_fn, white_params,
    objective = 'LMDE', turn_limit = np.deg2rad(30), bound = 100,
    theta_stack_low = None, theta_stack_high = None,
    walltime = None, xtol_rel = 0, ftol_rel = 0, ctol = 1e-6, 
    globalopt = False, n_draws = 5000, depth_penalty = False):

    # Select the approach objective
    if objective in ['LMDE', 'LE', 'LDE']:

        def objective(theta_stack, grad):
            return lmde_acquisition(theta_stack, r, x, 
                memory, feature_fn, white_params, 
                depth_penalty = depth_penalty)

    elif objective in ['MCPIE', 'MCJE', 'MCJIE']:

        S = np.random.normal(loc = 0., scale = 1., 
            size = (theta_stack_init.shape[0], n_draws))

        def objective(theta_stack, grad):
            return mcpie_acquisition(theta_stack, r, x, 
                memory, feature_fn, white_params, 
                n_draws = n_draws, S = S, depth_penalty = depth_penalty)

    elif objective in ['AMPIE', 'PIE', 'IE', 'SIE', 'MIE', 'SMIE']:

        def objective(theta_stack, grad):
            return ampie_acquisition(theta_stack, r, x, 
                memory, feature_fn, white_params, 
                depth_penalty = depth_penalty)

    # Define the path constraint
    def constraint(result, theta_stack, grad):
        result = path_bounds_model(theta_stack, r, x, feature_fn.Xq_ref, bound)

    # Obtain the number of parameters involvevd
    n_params = theta_stack_init.shape[0]

    # Prepare for global or local optimisation according to specification
    if globalopt:
        opt = nlopt.opt(nlopt.G_MLSL_LDS, n_params)
        local_opt = nlopt.opt(nlopt.LN_COBYLA , n_params)
        opt.set_local_optimizer(local_opt)
    else:
        opt = nlopt.opt(nlopt.LN_COBYLA , n_params)

    # Set lower and upper bound
    if theta_stack_low is not None:
        theta_stack_low[0] = theta_stack_init[0] - turn_limit
        opt.set_lower_bounds(theta_stack_low)
    if theta_stack_high is not None:
        theta_stack_high[0] = theta_stack_init[0] + turn_limit
        opt.set_upper_bounds(theta_stack_high)

    # Set tolerances
    if xtol_rel > 0:
        opt.set_xtol_rel(xtol_rel)
    if ftol_rel > 0:
        opt.set_ftol_rel(ftol_rel)
    
    # Set maximum optimisation time
    opt.set_maxtime(walltime)

    # Set the objective and constraint and optimise!
    opt.set_max_objective(objective)
    opt.add_inequality_mconstraint(constraint, ctol * np.ones(n_params))
    theta_stack_opt = opt.optimize(theta_stack_init)
    entropy_opt = opt.last_optimum_value()

    # Compute optimal path
    x_path_opt = forward_path_model(theta_stack_opt, r, x)

    # Replace the optimal coordinates with the closest query locations
    x_path_opt = feature_fn.closest_locations(x_path_opt)

    # Approximate the corresponding path angles
    theta_stack_opt = backward_path_model(x_path_opt, x)

    # Return path coordinates, path angles, and path entropy
    return x_path_opt, theta_stack_opt, entropy_opt

def random_path(theta_stack_init, r, x, memory, feature_fn, white_params, 
    bound = 100, chaos = False):

    # Seed randomly to guarantee no repeats from previous tests
    if chaos:
        np.random.seed(int(time.strftime("%M%S", time.gmtime())))

    # Randomly generate path angles that correspond to a valid path
    n_params = theta_stack_init.shape[0]
    theta_stack = np.random.uniform(0, 2 * np.pi, size = n_params)
    while path_bounds_model(theta_stack, r, x, feature_fn.Xq_ref, bound) > 0:
        theta_stack = np.random.uniform(0, 2 * pi, size = n_params)

    # Compute path coordinates
    x_path = forward_path_model(theta_stack, r, x)

    # Compute path entropy
    entropy = lmde_acquisition(theta_stack, r, x, 
                    memory, feature_fn, white_params)

    # Replace the optimal coordinates with the closest query locations
    x_path = feature_fn.closest_locations(x_path)

    # Approximate the corresponding path angles
    theta_stack = backward_path_model(x_path, x)
    
    # Return path coordinates, path angles, and path entropy
    return x_path, theta_stack, entropy

def fixed_path(theta_stack_init, r, x, memory, feature_fn, white_params,
    bound = 100, current_step = 0, turns = np.array([])):

    assert theta_stack_init.shape[0] == 1

    if current_step <= turns.shape[0]:
        turn_angle = turns[current_step]
    else:
        turn_angle = 0.0

    # Step forward
    theta_stack = np.mod(theta_stack_init + turn_angle, 2 * np.pi)
    x_path = forward_path_model(theta_stack, r, x)

    # Replace the optimal coordinates with the closest query locations
    x_path = feature_fn.closest_locations(x_path)

    # Approximate the corresponding path angles
    theta_stack = backward_path_model(x_path, x)

    # Compute path entropy
    entropy = lmde_acquisition(theta_stack, r, x, 
                    memory, feature_fn, white_params)

    # Return path coordinates, path angles, and path entropy
    return x_path, theta_stack, entropy

def forward_path_model(theta_stack, r, x):
    """
    Compute path coordinates from path angles, step size, and current location
    """
    # t = np.cumsum(theta_stack)
    # return x + np.array([np.cumsum(r * np.cos(t)), np.cumsum(r * np.sin(t))]).T
    theta = np.cumsum(theta_stack)
    x1_rel = np.cumsum(r * np.cos(theta))
    x2_rel = np.cumsum(r * np.sin(theta))
    return x + np.array([x1_rel, x2_rel]).T

def backward_path_model(X, x):
    """
    Approximates the path angles from the path coordinates
    """
    X_rel = X - x
    X_stack = np.concatenate((X_rel[[0]], np.diff(X_rel, axis = 0)), axis = 0)
    theta = np.arctan2(X_stack[:, 1], X_stack[:, 0])
    return np.concatenate((theta[[0]], np.diff(theta, axis = 0)), axis = 0)

def path_bounds_model(theta_stack, r, x, Xq_ref, bound):
    """
    Path Constraint
    """
    Xq = forward_path_model(theta_stack, r, x)
    c = cdist(Xq, Xq_ref).min(axis = 1) - bound
    logging.debug('Contraint Violation: {0}'.format(c))
    return c

def depth_entropy_penalty(Fq, depth_penalty = False):

    if depth_penalty:
        depth = Fq[:, 0]
        penalty = np.clip(40 - depth, 0, np.inf).sum()/10 + 1
        return 1/penalty
        logging.debug('Penalty: {0}'.format(penalty))
    else:
        return 1

def lmde_acquisition(theta_stack, r, x, memory, feature_fn, white_params, 
    depth_penalty = False):

    Xq = forward_path_model(theta_stack, r, x)
    Fq = feature_fn.extract(Xq)
    Fqw = feature_fn.whiten(Fq, white_params)
    entropy_penalty = depth_entropy_penalty(Fq, depth_penalty = depth_penalty)

    logging.info('Computing linearised model differential entropy...')
    start_time = time.clock()

    predictors = gp.classifier.query(memory, Fqw)
    yq_exp = gp.classifier.expectance(memory, predictors)
    yq_cov = gp.classifier.covariance(memory, predictors)
    entropy = gp.classifier.linearised_model_differential_entropy(yq_exp, yq_cov, memory)

    logging.debug('Linearised model differential entropy computational time: %.8f' % 
        (time.clock() - start_time))
    logging.debug('Angles (deg): {0} | Entropy: {1}'.format(
        np.rad2deg(theta_stack), entropy))
    if entropy_penalty == 1:
        return entropy
    else:
        return np.log(np.exp(entropy) * entropy_penalty)

def mcpie_acquisition(theta_stack, r, x, memory, feature_fn, white_params,
    n_draws = 1000, S = None, depth_penalty = False):

    Xq = forward_path_model(theta_stack, r, x)
    Fq = feature_fn.extract(Xq)
    Fqw = feature_fn.whiten(Fq, white_params)
    entropy_penalty = depth_entropy_penalty(Fq, depth_penalty = depth_penalty)

    logging.info('Computing Monte Carlo prediction information entropy...')
    start_time = time.clock()

    predictors = gp.classifier.query(memory, Fqw)
    yq_exp = gp.classifier.expectance(memory, predictors)
    yq_cov = gp.classifier.covariance(memory, predictors)
    entropy = gp.classifier.monte_carlo_prediction_information_entropy(yq_exp, yq_cov, memory, 
        n_draws = n_draws, S = S)

    logging.debug('Monte Carlo prediction information entropy computational time: %.8f' % 
        (time.clock() - start_time))
    logging.debug('Angles (deg): {0} | Entropy: {1}'.format(
        np.rad2deg(theta_stack), entropy))
    return entropy * entropy_penalty

def ampie_acquisition(theta_stack, r, x, memory, feature_fn, white_params, 
    depth_penalty = False):

    Xq = forward_path_model(theta_stack, r, x)
    Fq = feature_fn.extract(Xq)
    Fqw = feature_fn.whiten(Fq, white_params)
    entropy_penalty = depth_entropy_penalty(Fq, depth_penalty = depth_penalty)

    logging.info('Computing marginalised information entropy...')
    start_time = time.clock()

    yq_prob = gp.classifier.predict(Fqw, memory, fusemethod = 'EXCLUSION')
    entropy = gp.classifier.entropy(yq_prob).mean()

    logging.debug('Marginalised information entropy computational time: %.8f' % 
        (time.clock() - start_time))
    logging.debug('Angles (deg): {0} | Entropy: {1}'.format(
        np.rad2deg(theta_stack), entropy))
    return entropy * entropy_penalty

def shift_path(theta_stack, k_step = 1, theta_bounds = None):
    """
    Shift the stacking angles k_steps ahead
    """
    theta_stack_next = np.zeros(theta_stack.shape)
    theta_stack_next[1:-k_step] = theta_stack[(k_step + 1):]

    if theta_bounds is not None:
        np.clip(theta_stack_next, -theta_bounds - 1e-2, +theta_bounds + 1e-2, 
            out = theta_stack_next)
    theta_stack_next[0] = np.mod(theta_stack[:(k_step + 1)].sum(), (2 * np.pi))

    return theta_stack_next

def correct_lookahead_predictions(xq_abs_opt, learned_classifier, feature_fn, white_params, 
    decision_boundary):
    """
    Obtain the number of steps we can skip optimisation procedures for by 
    looking at the number of correct predictions ahead
    """
    # See how many correct predictions we have
    try:

        # Obtain the unique labels
        if isinstance(learned_classifier, list):
            y_unique = learned_classifier[0].cache.get('y_unique')
        else:
            y_unique = learned_classifier.cache.get('y_unique')

        # Whiten the features
        xqw_abs_opt = feature_fn(xq_abs_opt, white_params)

        # Obtain the predicted classes
        yq_pred = gp.classifier.classify(gp.classifier.predict(xqw_abs_opt, 
                learned_classifier), y_unique)

        # Obtain the true classes
        yq_true = gp.classifier.utils.make_decision(xq_abs_opt, 
            decision_boundary)

        # Obtain the number of correct predictions ahead
        k_step = np.arange(yq_pred.shape[0])[yq_pred != yq_true].argmin() + 1

        # Don't skip too much
        if k_step > yq_pred.shape[0]/2:
            k_step = int(yq_pred.shape[0]/2)

    # If anything goes wrong, perform no skips
    except Exception as e:
        logging.warning(e)
        k_step = 1

    return k_step

def average_marginalised_prediction_information_entropy(exp, covar, memory):
    return gp.classifier.entropy(gp.classifier.predict_from_latent(exp, covar, memory)).mean()

def get_acquisition_criterion(name):

    if name == 'LMDE':
        return gp.classifier.linearised_model_differential_entropy
    elif name == 'MCPIE':
        return gp.classifier.monte_carlo_prediction_information_entropy
    elif name == 'AMPIE':
        return average_marginalised_prediction_information_entropy

def compute_new_starting_location(start_indices, Xq, Fqw, memory, 
    kNN = 10, acquisition = 'LMDE'):

    acquisition_fn = get_acquisition_criterion(acquisition)

    Xq_cut = Xq[start_indices]
    Fqw_cut = Fqw[start_indices]

    def regional_score(xq):

        distances = cdist(xq, Xq)
        i_regions = np.argpartition(distances[0], -kNN)[-kNN:]

        predictors = gp.classifier.query(memory, Fqw[i_regions])
        exp = gp.classifier.expectance(memory, predictors)
        cov = gp.classifier.covariance(memory, predictors)

        score = acquisition_fn(exp, cov, memory)

        logging.debug('Regional score for {0} is {1}'.format(xq, score))

        return score

    scores = np.array([regional_score(Xq[[i]]) for i in start_indices])

    best_index = scores.argmax()

    xq_opt = Xq[[best_index]]
    logging.debug('Best location is {0} with score {1}'.format(xq_opt, scores[best_index]))
    return xq_opt
