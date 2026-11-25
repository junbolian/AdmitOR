import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    supply_p0 = params["supply_p0_origins"]
    supply_p1 = params["supply_p1_origins"]
    demand_p0 = params["demand_p0_dests"]
    demand_p1 = params["demand_p1_dests"]
    cost_p0 = params["cost_p0"]
    cost_p1 = params["cost_p1"]
    capacity = params["capacity"]

    I = range(6)
    J = range(6)

    model = pyo.ConcreteModel()

    model.x0 = pyo.Var(I, J, within=pyo.NonNegativeReals)
    model.x1 = pyo.Var(I, J, within=pyo.NonNegativeReals)

    def obj_rule(m):
        return sum(cost_p0[i][j] * m.x0[i, j] for i in I for j in J) + \
               sum(cost_p1[i][j] * m.x1[i, j] for i in I for j in J)

    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    model.supply0_con = pyo.Constraint(
        I, rule=lambda m, i: sum(m.x0[i, j] for j in J) == supply_p0[i])
    model.supply1_con = pyo.Constraint(
        I, rule=lambda m, i: sum(m.x1[i, j] for j in J) == supply_p1[i])
    model.demand0_con = pyo.Constraint(
        J, rule=lambda m, j: sum(m.x0[i, j] for i in I) == demand_p0[j])
    model.demand1_con = pyo.Constraint(
        J, rule=lambda m, j: sum(m.x1[i, j] for i in I) == demand_p1[j])
    model.cap_con = pyo.Constraint(
        I, J, rule=lambda m, i, j: m.x0[i, j] + m.x1[i, j] <= capacity[i][j])

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}