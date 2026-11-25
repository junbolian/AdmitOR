# IR: {"sets":{"P":[0,1,2,3],"C":[0,1,2,3,4]},"params":{"capacity":"capacity[p]","contract_demand":"contract_demand[c]","min_delivery":"min_delivery[p]","cost":"cost[p][c]"},"variables":{"x[p,c]":"nonnegative continuous delivery","y[p,c]":"binary contribution indicator"},"constraints":["sum(c in C) x[p,c] <= capacity[p] for p in P","sum(p in P) x[p,c] >= contract_demand[c] for c in C","sum(p in P) y[p,c] >= 2 for c in C","x[p,c] >= min_delivery[p]*y[p,c] for p in P,c in C","x[p,c] <= capacity[p]*y[p,c] for p in P,c in C"],"objective":"minimize sum(p in P,c in C) cost[p][c]*x[p,c]"}
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    capacity = params["capacity"]
    contract_demand = params["contract_demand"]
    min_delivery = params["min_delivery"]
    cost = params["cost"]

    model = pyo.ConcreteModel()
    model.P = pyo.RangeSet(0, 3)
    model.C = pyo.RangeSet(0, 4)

    model.capacity = pyo.Param(
        model.P, initialize={p: capacity[p] for p in model.P}
    )
    model.contract_demand = pyo.Param(
        model.C, initialize={c: contract_demand[c] for c in model.C}
    )
    model.min_delivery = pyo.Param(
        model.P, initialize={p: min_delivery[p] for p in model.P}
    )
    model.cost = pyo.Param(
        model.P,
        model.C,
        initialize={(p, c): cost[p][c] for p in model.P for c in model.C},
    )

    model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

    def capacity_rule(mod, p):
        return sum(mod.x[p, c] for c in mod.C) <= mod.capacity[p]

    model.capacity_limit = pyo.Constraint(model.P, rule=capacity_rule)

    def demand_rule(mod, c):
        return sum(mod.x[p, c] for p in mod.P) >= mod.contract_demand[c]

    model.demand_requirement = pyo.Constraint(model.C, rule=demand_rule)

    def contributor_rule(mod, c):
        return sum(mod.y[p, c] for p in mod.P) >= 2

    model.contributor_requirement = pyo.Constraint(
        model.C, rule=contributor_rule
    )

    def minimum_rule(mod, p, c):
        return mod.x[p, c] >= mod.min_delivery[p] * mod.y[p, c]

    model.minimum_contribution = pyo.Constraint(
        model.P, model.C, rule=minimum_rule
    )

    def linking_rule(mod, p, c):
        return mod.x[p, c] <= mod.capacity[p] * mod.y[p, c]

    model.contribution_link = pyo.Constraint(
        model.P, model.C, rule=linking_rule
    )

    model.total_cost = pyo.Objective(
        expr=sum(
            model.cost[p, c] * model.x[p, c]
            for p in model.P
            for c in model.C
        ),
        sense=pyo.minimize,
    )

    try:
        Highs().solve(model)
    except RuntimeError:
        return {"objective": None, "status": "solve_failed"}

    try:
        obj_val = float(pyo.value(model.total_cost))
    except (ValueError, TypeError):
        return {"objective": None, "status": "objective_unavailable"}

    return {"objective": obj_val, "status": "optimal"}