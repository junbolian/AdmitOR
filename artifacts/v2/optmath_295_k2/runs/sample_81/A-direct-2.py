import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    crate_weight = params["crate_weight"]
    truck_capacity = params["truck_capacity"]

    n_crates = 10
    n_trucks = 10

    model = pyo.ConcreteModel()

    model.CRATES = pyo.RangeSet(0, n_crates - 1)
    model.TRUCKS = pyo.RangeSet(0, n_trucks - 1)

    model.x = pyo.Var(model.CRATES, model.TRUCKS, domain=pyo.Binary)
    model.y = pyo.Var(model.TRUCKS, domain=pyo.Binary)

    def assign_rule(m, c):
        return sum(m.x[c, t] for t in m.TRUCKS) == 1

    model.assign_con = pyo.Constraint(model.CRATES, rule=assign_rule)

    def capacity_rule(m, t):
        return sum(crate_weight * m.x[c, t] for c in m.CRATES) <= truck_capacity * m.y[t]

    model.capacity_con = pyo.Constraint(model.TRUCKS, rule=capacity_rule)

    def link_rule(m, c, t):
        return m.x[c, t] <= m.y[t]

    model.link_con = pyo.Constraint(model.CRATES, model.TRUCKS, rule=link_rule)

    model.obj = pyo.Objective(expr=sum(model.y[t] for t in model.TRUCKS), sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}