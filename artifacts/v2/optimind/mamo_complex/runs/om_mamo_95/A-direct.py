import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    warehouses = [1, 2, 3, 4, 5, 6]
    pairs = [(i, j) for i in warehouses for j in warehouses if i != j]

    supply = {i: params[f"supply"] if isinstance(params.get("supply"), (int, float)) else params["supply"][i - 1] for i in warehouses}
    demand = {i: params[f"demand"] if isinstance(params.get("demand"), (int, float)) else params["demand"][i - 1] for i in warehouses}
    cost = {(i, j): params[f"cost_{i}_{j}"] for (i, j) in pairs}

    model = pyo.ConcreteModel()
    model.W = pyo.Set(initialize=warehouses)
    model.P = pyo.Set(initialize=pairs, dimen=2)

    model.x = pyo.Var(model.P, domain=pyo.NonNegativeReals)

    def flow_rule(mdl, i):
        inflow = sum(mdl.x[(j, i)] for j in warehouses if j != i)
        outflow = sum(mdl.x[(i, j)] for j in warehouses if j != i)
        return supply[i] + inflow - outflow >= demand[i]

    model.flow = pyo.Constraint(model.W, rule=flow_rule)

    def obj_rule(mdl):
        return sum(cost[(i, j)] * mdl.x[(i, j)] for (i, j) in pairs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Feasibility pre-check: total supply must cover total demand
    if sum(supply[i] for i in warehouses) < sum(demand[i] for i in warehouses):
        return {"objective": None, "status": "infeasible"}

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}