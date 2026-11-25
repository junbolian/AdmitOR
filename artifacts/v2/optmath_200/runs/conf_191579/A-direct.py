import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    periods = list(range(4))

    # Time-varying data are given in the problem as per-period vectors.
    demand_A = [51, 50, 62, 79]
    demand_B = [56, 70, 70, 68]
    prod_cost_A = [43, 45, 41, 40]
    prod_cost_B = [41, 41, 40, 41]
    setup_cost_A = [1167, 1375, 1385, 1378]
    setup_cost_B = [1065, 1075, 1111, 1405]
    hold_cost_A = [4, 4, 4, 4]
    hold_cost_B = [4, 4, 5, 5]
    capacity = [852, 900, 825, 875]
    prod_ub_A = [242, 191, 141, 79]
    prod_ub_B = [264, 208, 138, 68]

    # Scalar structural parameters read from params (may override if provided as scalars)
    usage_A = params["usage_A"]
    usage_B = params["usage_B"]

    # If scalar params are provided (e.g., single value), distribute; if lists, use as-is.
    def as_vec(val, default):
        if isinstance(val, (list, tuple)):
            return list(val)
        return [val] * 4

    demand_A = as_vec(params.get("demand_A", demand_A), demand_A)
    demand_B = as_vec(params.get("demand_B", demand_B), demand_B)
    prod_cost_A = as_vec(params.get("prod_cost_A", prod_cost_A), prod_cost_A)
    prod_cost_B = as_vec(params.get("prod_cost_B", prod_cost_B), prod_cost_B)
    setup_cost_A = as_vec(params.get("setup_cost_A", setup_cost_A), setup_cost_A)
    setup_cost_B = as_vec(params.get("setup_cost_B", setup_cost_B), setup_cost_B)
    hold_cost_A = as_vec(params.get("hold_cost_A", hold_cost_A), hold_cost_A)
    hold_cost_B = as_vec(params.get("hold_cost_B", hold_cost_B), hold_cost_B)
    capacity = as_vec(params.get("capacity", capacity), capacity)
    prod_ub_A = as_vec(params.get("prod_ub_A", prod_ub_A), prod_ub_A)
    prod_ub_B = as_vec(params.get("prod_ub_B", prod_ub_B), prod_ub_B)

    model = pyo.ConcreteModel()
    model.T = pyo.Set(initialize=periods)

    model.prod_A = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.prod_B = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.inv_A = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.inv_B = pyo.Var(model.T, domain=pyo.NonNegativeReals)
    model.setup_A = pyo.Var(model.T, domain=pyo.Binary)
    model.setup_B = pyo.Var(model.T, domain=pyo.Binary)

    def balance_A_rule(m, t):
        prev = 0 if t == 0 else m.inv_A[t - 1]
        return m.inv_A[t] == prev + m.prod_A[t] - demand_A[t]

    def balance_B_rule(m, t):
        prev = 0 if t == 0 else m.inv_B[t - 1]
        return m.inv_B[t] == prev + m.prod_B[t] - demand_B[t]

    model.balance_A = pyo.Constraint(model.T, rule=balance_A_rule)
    model.balance_B = pyo.Constraint(model.T, rule=balance_B_rule)

    def capacity_rule(m, t):
        return usage_A * m.prod_A[t] + usage_B * m.prod_B[t] <= capacity[t]

    model.capacity_con = pyo.Constraint(model.T, rule=capacity_rule)

    def link_A_rule(m, t):
        return m.prod_A[t] <= prod_ub_A[t] * m.setup_A[t]

    def link_B_rule(m, t):
        return m.prod_B[t] <= prod_ub_B[t] * m.setup_B[t]

    model.link_A = pyo.Constraint(model.T, rule=link_A_rule)
    model.link_B = pyo.Constraint(model.T, rule=link_B_rule)

    def obj_rule(m):
        return sum(
            prod_cost_A[t] * m.prod_A[t]
            + prod_cost_B[t] * m.prod_B[t]
            + setup_cost_A[t] * m.setup_A[t]
            + setup_cost_B[t] * m.setup_B[t]
            + hold_cost_A[t] * m.inv_A[t]
            + hold_cost_B[t] * m.inv_B[t]
            for t in m.T
        )

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}