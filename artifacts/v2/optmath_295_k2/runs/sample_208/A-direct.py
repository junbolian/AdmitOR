import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    resource_weights = params["resource_weights"]
    facility_capacity = params["facility_capacity"]

    num_resources = len(resource_weights)
    num_facilities = num_resources

    model = pyo.ConcreteModel()

    model.RESOURCES = pyo.RangeSet(0, num_resources - 1)
    model.FACILITIES = pyo.RangeSet(0, num_facilities - 1)

    model.assign = pyo.Var(model.RESOURCES, model.FACILITIES, domain=pyo.Binary)
    model.use_facility = pyo.Var(model.FACILITIES, domain=pyo.Binary)

    def assign_rule(m, r):
        return sum(m.assign[r, f] for f in m.FACILITIES) == 1
    model.assign_con = pyo.Constraint(model.RESOURCES, rule=assign_rule)

    def capacity_rule(m, f):
        return sum(resource_weights[r] * m.assign[r, f] for r in m.RESOURCES) <= facility_capacity * m.use_facility[f]
    model.capacity_con = pyo.Constraint(model.FACILITIES, rule=capacity_rule)

    def linking_rule(m, r, f):
        return m.assign[r, f] <= m.use_facility[f]
    model.linking_con = pyo.Constraint(model.RESOURCES, model.FACILITIES, rule=linking_rule)

    def obj_rule(m):
        return sum(m.use_facility[f] for f in m.FACILITIES)
    model.total_facilities = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_facilities))
    return {"objective": obj_val, "status": "optimal"}