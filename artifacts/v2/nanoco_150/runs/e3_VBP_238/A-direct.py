import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    f_cap = params["flammability_capacity_per_vehicle"]
    t_cap = params["toxicity_capacity_per_vehicle"]
    f_dem = params["flammability_demand"]
    t_dem = params["toxicity_demand"]

    shipments = list(range(len(f_dem)))
    vehicles = list(range(len(f_dem)))

    model = pyo.ConcreteModel()

    model.S = pyo.Set(initialize=shipments)
    model.V = pyo.Set(initialize=vehicles)

    model.x = pyo.Var(model.S, model.V, domain=pyo.Binary)
    model.y = pyo.Var(model.V, domain=pyo.Binary)

    def obj_rule(m):
        return sum(m.y[j] for j in m.V)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def assign_rule(m, i):
        return sum(m.x[i, j] for j in m.V) == 1

    model.assign_con = pyo.Constraint(model.S, rule=assign_rule)

    def f_cap_rule(m, j):
        return sum(f_dem[i] * m.x[i, j] for i in m.S) <= f_cap * m.y[j]

    model.f_cap_con = pyo.Constraint(model.V, rule=f_cap_rule)

    def t_cap_rule(m, j):
        return sum(t_dem[i] * m.x[i, j] for i in m.S) <= t_cap * m.y[j]

    model.t_cap_con = pyo.Constraint(model.V, rule=t_cap_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}