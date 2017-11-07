import numpy as np
import matplotlib.pylab as plt

from models.linear_gaussian_model import LinearGaussianModel
from parameter.mcmc.metropolis_hastings import MetropolisHastings
from state.kalman_methods.standard import KalmanMethods
from state.kalman_methods.cython import KalmanMethodsCython
from state.particle_methods.standard import ParticleMethods
from state.particle_methods.cython_lgss import ParticleMethodsCythonLGSS

def run(cython_code=True, filter_method='kalman', alg_type='mh0', plotting=True,
        file_tag=None, **kwargs):

    # System model
    sys_model = LinearGaussianModel()
    sys_model.params['mu'] = 0.20
    sys_model.params['phi'] = 0.50
    sys_model.params['sigma_v'] = 1.00
    sys_model.params['sigma_e'] = 0.50
    sys_model.no_obs = 500
    sys_model.initial_state = 0.0
    sys_model.import_data(file_name="../data/linear_gaussian_model/linear_gaussian_model_T500_midSNR.csv")

    # Inference model
    sys_model.fix_true_params()
    sys_model.create_inference_model(params_to_estimate = ('mu', 'phi', 'sigma_v'))
    print(sys_model)

    # Kalman filter and smoother
    if cython_code:
        kf = KalmanMethodsCython()
    else:
        kf = KalmanMethods()

    if kwargs:
        kf.settings.update(kwargs)

    # Particle filter and smoother
    if cython_code:
        pf = ParticleMethodsCythonLGSS()
    else:
        pf = ParticleMethods()

    pf.settings.update({'no_particles': 1000,
                        'fixed_lag': 10,
                        'verbose': False})

    if kwargs:
        pf.settings.update(kwargs)

    # Metropolis-Hastings
    hessian_estimate = np.array([[ 0.00397222, -0.00228247,  0.00964908],
                                 [-0.00228247,  0.00465944, -0.00961161],
                                 [ 0.00964908, -0.00961161,  0.05049018]])

    mh_settings = {'no_iters': 2500,
                   'no_burnin_iters': 500,
                   'base_hessian': hessian_estimate,
                   'initial_params': (0.0, 0.1, 0.2),
                   'verbose': False
                   }
    if kwargs:
        mh_settings.update(kwargs)
    mh = MetropolisHastings(sys_model, alg_type, mh_settings)

    if filter_method is 'kalman':
        if alg_type is 'mh0':
            mh.settings['step_size'] = 2.38 / np.sqrt(sys_model.no_params_to_estimate)
        elif alg_type is 'mh1':
            mh.settings['step_size'] = 1.38 / np.sqrt(sys_model.no_params_to_estimate**(1/3))
        elif alg_type is 'mh2':
            mh.settings['step_size'] = 0.8
        else:
            raise NameError("Unknown alg_type (mh0/mh1/mh2/qmh).")

        mh.run(kf)

    elif filter_method is 'particle':
        if alg_type is 'mh0':
            mh.settings['step_size'] = 2.562 / np.sqrt(sys_model.no_params_to_estimate)
        elif alg_type is 'mh1':
            mh.settings['step_size'] = 1.125 / np.sqrt(sys_model.no_params_to_estimate**(1/3))
        elif alg_type is 'mh2':
            mh.settings['step_size'] = 0.8
        else:
            raise NameError("Unknown alg_type (mh0/mh1/mh2/qmh).")
        mh.run(pf)
    else:
        raise NameError("Unknown filter_method (kalman/particle).")

    if plotting:
        mh.plot()
    else:
        sim_name = 'test_linear_gaussian_' + alg_type + '_' + filter_method
        if file_tag:
            sim_name += '_' + file_tag
        mh.save_to_file(output_path='../results-tests/mh-linear-gaussian/',
                        sim_name=sim_name,
                        sim_desc='...')