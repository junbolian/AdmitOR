import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    resource_weights = params["resource_weights"]
    center_capacity = params["center_capacity"]
    num_resources = params["num_resources"]
    num_centers_available = params["num_centers_available"]

    model = pyo.ConcreteModel()

    model.RESOURCES = pyo.RangeSet(0, num_resources - 1)
    model.CENTERS = pyo.RangeSet(0, num_centers_available - 1)

    # x[r, c] = 1 if resource r assigned to center c
    model.x = pyo.Var(model.RESOURCES, model.CENTERS, domain=pyo.Binary)
    # y[c] = 1 if center c is used
    model.y = pyo.Var(model.CENTERS, domain=pyo.Binary)

    def objective_rule(m):
        return sum(m.y[c] for c in m.CENTERS)
    model.total_centers = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    # Each resource assigned to exactly one center
    def assign_rule(m, r):
        return sum(m.x[r, c] for c in m.CENTERS) == 1
    model.assign = pyo.Constraint(model.RESOURCES, rule=assign_rule)

    # Capacity per center
    def capacity_rule(m, c):
        return sum(resource_weights[r] * m.x[r, c] for r in m.RESOURCES) <= center_capacity * m.y[c]
    model.capacity = pyo.Constraint(model.CENTERS, rule=capacity_rule)

    # Link: resource can be assigned to center c only if y[c] = 1
    def link_rule(m, r, c):
        return m.x[r, c] <= m.y[c]
    model.link = pyo.Constraint(model.RESOURCES, model.CENTERS, rule=link_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_centers))
    return {"objective": obj_val, "status": "optimal"}