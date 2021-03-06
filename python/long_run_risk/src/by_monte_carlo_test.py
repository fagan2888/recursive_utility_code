"""
Monte Carlo based computation of the test value, BY model.

"""

from numpy.random import randn
from numba import jit, njit, f8, prange

from by_model import *


@njit(f8[:](f8[:], f8[:]))
def update_state(x, c_params):

    μ_c, ρ, ϕ_z, v, d, ϕ_σ = c_params

    z, σ = x

    # update state
    σ2 = v * σ**2 + d + ϕ_σ * randn()
    σ = np.sqrt(max(σ2, 0))
    z = ρ * z + ϕ_z * σ * randn()

    return np.array((z, σ))


@njit(f8(f8[:], f8[:], f8[:]))
def eval_kappa(x, y, c_params):
    """
    Computes kappa_{t+1} given z_t and sigma_t
    """
    μ_c, ρ, ϕ_z, v, d, ϕ_σ = c_params
    z, σ = x

    return μ_c + z + σ * randn()



def by_function_factory(by,  parallelization_flag=False):
    """
    Produces functions that compute the stability test value Lambda 
    via Monte Carlo.

    """

    β, γ, ψ = by.β, by.γ, by.ψ 
    μ_c, ρ, ϕ_z, v, d, ϕ_σ = by.μ_c, by.ρ, by.ϕ_z, by.v, by.d, by.ϕ_σ  

    z = 0.0
    σ = d / (1 - v)
    initial_state = np.array((z, σ))

    @njit(parallel=parallelization_flag)
    def by_compute_stat_mc(initial_state=initial_state,
                         n=1000, 
                         m=1000,
                         seed=1234,
                         burn_in=500):
        """
        Compute the stability test value Lambda via Monte Carlo.

        """
        c_params = μ_c, ρ, ϕ_z, v, d, ϕ_σ 
        c_params = np.array(c_params)

        np.random.seed(seed)

        # Implement some burn in for the state
        x = initial_state
        for t in range(burn_in):
            x = update_state(x, c_params)

        # Compute samples for MC stat
        yn_vals = np.empty(m)
        θ = (1 - γ) / (1 - 1/ψ)

        for i in prange(m):
            kappa_sum = 0.0

            for t in range(n):
                y = update_state(x, c_params)
                kappa_sum += eval_kappa(x, y, c_params)
                x = y

            yn_vals[i] = np.exp((1-γ) * kappa_sum)

        mean_yns = np.mean(yn_vals)
        Lm = β * mean_yns**(1 / (n * θ))

        return Lm 

    return by_compute_stat_mc



