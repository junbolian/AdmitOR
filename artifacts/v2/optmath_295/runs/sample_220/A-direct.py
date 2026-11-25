import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    n = 5
    hub_ids = list(range(n))
    net = {
        0: params["demand_hub0"],
        1: params["demand_hub1"],
        2: -params["supply_hub2"],
        3: -params["supply_hub3"],
        4: -params["supply_hub4"],
    }
    links = [(i, j) for i in hub_ids for j in hub_ids if i != j]

    def _val(spec, i, j):
        lo, hi = spec
        if hi == lo:
            return lo
        scaled = (i * n + j) % (hi - lo + 1)
        return lo + scaled

    fixed_cost = {}
    var_cost = {}
    cap = {}
    for (i, j) in links:
        fixed_cost[(i, j)] = _val(params["fixed_cost_range"], i, j)
        var_cost[(i, j)] = _val(params["variable_cost_range"], i, j)
        cap[(i, j)] = _val(params["capacity_range"], i, j)

    model = pyo.ConcreteModel()
    model.hubs = pyo.Set(initialize=hub_ids)
    model.links = pyo.Set(initialize=links, dimen=2)

    model.x = pyo.Var(model.links, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.links, domain=pyo.Binary)

    def flow_rule(md, i, j):
        return md.x[(i, j)] <= cap[(i, j)] * md.y[(i, j)]
    model.flow_cap = pyo.Constraint(model.links, rule=flow_rule)

    def balance_rule(md, k):
        return sum(md.x[(k, j)] for j in hub_ids if j != k) - \
               sum(md.x[(i, k)] for i in hub_ids if i != k) == net[k]
    model.balance = pyo.Constraint(model.hubs, rule=balance_rule)

    def obj_rule(md):
        return sum(fixed_cost[(i, j)] * md.y[(i, j)] +
                   var_cost[(i, j)] * md.x[(i, j)] for (i, j) in links)
    model.objective = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    try:
        Highs().solve(model)
        obj_val = float(pyo.value(model.objective))
    except Exception as e:
        return {"objective": None, "status": "solver failure: " + str(e)[:60]}

    return {"objective": obj_val, "status": "optimal"}