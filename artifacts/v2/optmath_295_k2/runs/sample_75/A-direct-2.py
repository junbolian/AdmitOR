import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs

def solve(params):
    item_labels = [f"item_{i}" for i in range(13)]

    model = pyo.ConcreteModel()
    model.item_set = pyo.Set(initialize=item_labels, ordered=True)

    model.x = pyo.Var(model.item_set, domain=pyo.NonNegativeReals)

    def _obj_rule(mdl):
        return sum(params["profit"][i] * mdl.x[i] for i in mdl.item_set)
    model.total_profit = pyo.Objective(rule=_obj_rule, sense=pyo.maximize)

    def _resource_rule(mdl):
        return sum(params["resource_rate"][i] * mdl.x[i] for i in mdl.item_set) <= params["resource_capacity"]
    model.resource_con = pyo.Constraint(rule=_resource_rule)

    def _cap_rule(mdl, i):
        return mdl.x[i] <= params["production_capacity"][i]
    model.cap_con = pyo.Constraint(model.item_set, rule=_cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_profit))
    return {"objective": obj_val, "status": "optimal"}