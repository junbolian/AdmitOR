import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    num_facilities = 8
    num_dcs = 10

    supply = [params["supply"][i] for i in range(num_facilities)]
    demand = [params["demand"][j] for j in range(num_dcs)]

    given_cost = {}
    given_cap = {}
    for key in params:
        if key.startswith("cost_"):
            parts = key.split("_")
            given_cost[(int(parts[1]), int(parts[2]))] = params[key]
        elif key.startswith("cap_"):
            parts = key.split("_")
            given_cap[(int(parts[1]), int(parts[2]))] = params[key]

    default_cost = 0.0
    if given_cost:
        default_cost = max(given_cost.values()) * 10.0

    default_cap = None
    if given_cap:
        default_cap = max(given_cap.values()) * 10.0

    cost = {}
    cap = {}
    for i in range(num_facilities):
        for j in range(num_dcs):
            cost[(i, j)] = given_cost.get((i, j), default_cost)
            cap[(i, j)] = given_cap.get((i, j), default_cap)

    model = pyo.ConcreteModel()

    model.F = pyo.RangeSet(0, num_facilities - 1)
    model.D = pyo.RangeSet(0, num_dcs - 1)

    model.x = pyo.Var(model.F, model.D, domain=pyo.NonNegativeReals)

    def cap_rule(mdl, i, j):
        if cap[(i, j)] is None:
            return pyo.Constraint.Skip
        return mdl.x[i, j] <= cap[(i, j)]
    model.cap_constraint = pyo.Constraint(model.F, model.D, rule=cap_rule)

    def supply_rule(mdl, i):
        return sum(mdl.x[i, j] for j in mdl.D) == supply[i]
    model.supply_constraint = pyo.Constraint(model.F, rule=supply_rule)

    def demand_rule(mdl, j):
        return sum(mdl.x[i, j] for i in mdl.F) == demand[j]
    model.demand_constraint = pyo.Constraint(model.D, rule=demand_rule)

    def obj_rule(mdl):
        return sum(cost[(i, j)] * mdl.x[i, j] for i in mdl.F for j in mdl.D)
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}