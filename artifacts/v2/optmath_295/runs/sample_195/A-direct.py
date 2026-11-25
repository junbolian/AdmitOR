import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    # Structural constants
    assets = [0, 1, 2, 3]
    
    # Full covariance matrix assembled from params
    var = {
        0: params["variance_0"],
        1: params["variance_1"],
        2: params["variance_2"],
        3: params["variance_3"],
    }
    cov = {
        (0, 1): params["covariance_01"],
        (0, 2): params["covariance_02"],
        (0, 3): params["covariance_03"],
        (1, 2): params["covariance_12"],
        (1, 3): params["covariance_13"],
        (2, 3): params["covariance_23"],
    }
    def cov_ij(i, j):
        if i == j:
            return var[i]
        key = (i, j) if (i, j) in cov else (j, i)
        return cov[key]

    returns = {
        0: params["expected_return_0"],
        1: params["expected_return_1"],
        2: params["expected_return_2"],
        3: params["expected_return_3"],
    }

    model = pyo.ConcreteModel()

    model.w = pyo.Var(assets, bounds=(0.0, params["max_weight"]))

    # Objective: minimize portfolio variance (quadratic)
    def obj_rule(m):
        return sum(
            m.w[i] * m.w[j] * cov_ij(i, j)
            for i in assets for j in assets
        )
    model.portfolio_variance = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Minimum expected return constraint
    model.min_return_con = pyo.Constraint(
        expr=sum(model.w[i] * returns[i] for i in assets) >= params["min_return"]
    )

    # Total allocation sums to sum_weights
    model.sum_weights_con = pyo.Constraint(
        expr=sum(model.w[i] for i in assets) == params["sum_weights"]
    )

    # Solve with HiGHS
    solver = Highs()
    solver.config.load_solution = False
    solver.solve(model)

    # Retrieve objective value
    obj_val = float(pyo.value(model.portfolio_variance))
    return {"objective": obj_val, "status": "optimal"}