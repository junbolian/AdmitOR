import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    cycle_time = params["cycle_time"]
    n = len(cycle_time)

    model = pyo.ConcreteModel()
    model.arms = pyo.RangeSet(0, n - 1)
    model.stations = pyo.RangeSet(0, n - 1)

    model.x = pyo.Var(model.arms, model.stations, domain=pyo.Binary)

    def obj_rule(m):
        return sum(cycle_time[i][j] * m.x[i, j] for i in m.arms for j in m.stations)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def arm_rule(m, i):
        return sum(m.x[i, j] for j in m.stations) == 1

    model.arm_assign = pyo.Constraint(model.arms, rule=arm_rule)

    def station_rule(m, j):
        return sum(m.x[i, j] for i in m.arms) == 1

    model.station_assign = pyo.Constraint(model.stations, rule=station_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}