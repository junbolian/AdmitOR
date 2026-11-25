import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_subcontractors = params["num_subcontractors"]
    num_phases = params["num_phases"]

    labor_limit = [
        params["labor_limit_S1"],
        params["labor_limit_S2"],
        params["labor_limit_S3"],
    ]
    labor_req = params["labor_req"]
    bid_price = params["bid_price"]

    model = pyo.ConcreteModel()

    model.S = pyo.RangeSet(0, num_subcontractors - 1)
    model.P = pyo.RangeSet(0, num_phases - 1)

    model.x = pyo.Var(model.S, model.P, domain=pyo.Binary)

    def objective_rule(m):
        return sum(bid_price[s][p] * m.x[s, p] for s in m.S for p in m.P)

    model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

    def assign_rule(m, p):
        return sum(m.x[s, p] for s in m.S) == 1

    model.assign_con = pyo.Constraint(model.P, rule=assign_rule)

    def labor_rule(m, s):
        return sum(labor_req[s][p] * m.x[s, p] for p in m.P) <= labor_limit[s]

    model.labor_con = pyo.Constraint(model.S, rule=labor_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}