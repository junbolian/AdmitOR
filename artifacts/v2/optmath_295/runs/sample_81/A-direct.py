import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    crate_weight = params["crate_weight"]
    truck_capacity = params["truck_capacity"]
    num_crates = params["num_crates"]
    num_trucks = params["num_trucks"]

    model = pyo.ConcreteModel()

    model.CRATES = pyo.Set(initialize=range(num_crates))
    model.TRUCKS = pyo.Set(initialize=range(num_trucks))

    model.assign = pyo.Var(model.CRATES, model.TRUCKS, domain=pyo.Binary)
    model.used = pyo.Var(model.TRUCKS, domain=pyo.Binary)

    def crate_assigned_once_rule(m, c):
        return sum(m.assign[c, t] for t in m.TRUCKS) == 1

    model.crate_assigned_once = pyo.Constraint(
        model.CRATES, rule=crate_assigned_once_rule
    )

    def capacity_rule(m, t):
        return sum(crate_weight * m.assign[c, t] for c in m.CRATES) <= (
            truck_capacity * m.used[t]
        )

    model.capacity = pyo.Constraint(model.TRUCKS, rule=capacity_rule)

    def link_rule(m, c, t):
        return m.assign[c, t] <= m.used[t]

    model.link = pyo.Constraint(model.CRATES, model.TRUCKS, rule=link_rule)

    model.obj = pyo.Objective(
        expr=sum(model.used[t] for t in model.TRUCKS), sense=pyo.minimize
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}