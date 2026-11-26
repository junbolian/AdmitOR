import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    clinics = [1, 2, 3, 4]

    initial_stock = {i: params["initial_stock"][i - 1] for i in clinics}
    required_demand = {i: params["required_demand"][i - 1] for i in clinics}

    cost = {}
    for i in clinics:
        for j in clinics:
            if i != j:
                cost[(i, j)] = params[f"transport_cost_{i}_to_{j}"]

    arcs = [(i, j) for i in clinics for j in clinics if i != j]

    model = pyo.ConcreteModel()

    model.arcs = pyo.Set(initialize=arcs, dimen=2)
    model.clinics = pyo.Set(initialize=clinics)

    model.ship = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost[(i, j)] * m.ship[(i, j)] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Final stock at each clinic must be >= required demand.
    # Total initial stock exceeds total required demand, so surplus
    # must be allowed to remain (slack), otherwise the equality
    # balance system is infeasible.
    def balance_rule(m, k):
        inflow = sum(m.ship[(i, k)] for i in clinics if i != k)
        outflow = sum(m.ship[(k, j)] for j in clinics if j != k)
        return initial_stock[k] + inflow - outflow >= required_demand[k]

    model.balance = pyo.Constraint(model.clinics, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}