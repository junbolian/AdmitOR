import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_weights = params["supply_weights"]
    capacity = params["hospital_capacity"]

    num_supplies = len(supply_weights)
    num_hospitals = num_supplies

    model = pyo.ConcreteModel()

    model.SUPPLIES = pyo.RangeSet(0, num_supplies - 1)
    model.HOSPITALS = pyo.RangeSet(0, num_hospitals - 1)

    model.assign = pyo.Var(model.SUPPLIES, model.HOSPITALS, domain=pyo.Binary)
    model.use_hospital = pyo.Var(model.HOSPITALS, domain=pyo.Binary)

    def obj_rule(mdl):
        return sum(mdl.use_hospital[j] for j in mdl.HOSPITALS)
    model.total_hospitals_used = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(mdl, i):
        return sum(mdl.assign[i, j] for j in mdl.HOSPITALS) == 1
    model.assign_con = pyo.Constraint(model.SUPPLIES, rule=assign_rule)

    def cap_rule(mdl, j):
        return sum(supply_weights[i] * mdl.assign[i, j] for i in mdl.SUPPLIES) <= capacity * mdl.use_hospital[j]
    model.cap_con = pyo.Constraint(model.HOSPITALS, rule=cap_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_hospitals_used))
    return {'objective': obj_val, 'status': 'optimal'}