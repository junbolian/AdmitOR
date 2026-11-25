import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    restaurants = [0, 1]
    shifts = [0, 1]
    employees = [0, 1, 2, 3, 4, 5]

    skilled = {1, 2, 3, 4}

    unavailable = {
        (0, 0, 0), (0, 0, 1), (0, 1, 0), (0, 1, 1),
        (3, 0, 1), (3, 1, 1),
    }

    pref_cost = {
        1: params["pref_cost_emp1"],
        2: params["pref_cost_emp2"],
        3: params["pref_cost_emp3"],
        4: params["pref_cost_emp4"],
    }

    demand = {
        (0, 0): params["demand_R0_S0"],
        (0, 1): params["demand_R0_S1"],
        (1, 0): params["demand_R1_S0"],
        (1, 1): params["demand_R1_S1"],
    }

    penalty = params["penalty_per_unfulfilled"]

    model = pyo.ConcreteModel()

    model.R = pyo.Set(initialize=restaurants)
    model.S = pyo.Set(initialize=shifts)
    model.E = pyo.Set(initialize=employees)

    def allowed_triples():
        for e in employees:
            for r in restaurants:
                for s in shifts:
                    if (e, r, s) in unavailable:
                        continue
                    if demand[(r, s)] > 0 and e not in skilled:
                        continue
                    yield (e, r, s)

    model.ASG = pyo.Set(dimen=3, initialize=list(allowed_triples()))
    model.RS = pyo.Set(dimen=2, initialize=[(r, s) for r in restaurants for s in shifts])

    model.x = pyo.Var(model.ASG, domain=pyo.Binary)
    model.unfilled = pyo.Var(model.RS, domain=pyo.NonNegativeIntegers)

    def demand_rule(model, r, s):
        assigned = sum(
            model.x[e, r, s] for e in employees if (e, r, s) in model.ASG
        )
        return assigned + model.unfilled[r, s] == demand[(r, s)]

    model.demand_con = pyo.Constraint(model.RS, rule=demand_rule)

    def at_most_one_rule(model, e):
        return sum(
            model.x[ee, r, s] for (ee, r, s) in model.ASG if ee == e
        ) <= 1

    model.at_most_one = pyo.Constraint(model.E, rule=at_most_one_rule)

    def obj_rule(model):
        assign_cost = sum(
            pref_cost[e] * model.x[e, r, s]
            for (e, r, s) in model.ASG
            if e in pref_cost
        )
        penalty_cost = sum(
            penalty * model.unfilled[r, s] for (r, s) in model.RS
        )
        return assign_cost + penalty_cost

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}