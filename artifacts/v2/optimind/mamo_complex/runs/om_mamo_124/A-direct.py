import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    num_cities = int(params["num_cities"])
    nodes = list(range(1, num_cities + 1))

    cost = {}
    for i in nodes:
        for j in nodes:
            if i != j:
                cost[(i, j)] = params["cost_{}{}".format(i, j)]

    arcs = list(cost.keys())

    model = pyo.ConcreteModel()

    model.cities = pyo.Set(initialize=nodes)
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    def obj_rule(model):
        return sum(cost[(i, j)] * model.x[(i, j)] for (i, j) in arcs)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def leave_rule(model, i):
        return sum(model.x[(i, j)] for j in nodes if j != i) == 1

    model.leave = pyo.Constraint(model.cities, rule=leave_rule)

    def arrive_rule(model, j):
        return sum(model.x[(i, j)] for i in nodes if i != j) == 1

    model.arrive = pyo.Constraint(model.cities, rule=arrive_rule)

    # Subtour elimination via MTZ formulation
    model.order = pyo.Var(model.cities, bounds=(1, num_cities))

    model.start_order = pyo.Constraint(expr=model.order[1] == 1)

    def mtz_rule(model, i, j):
        if i != j and i != 1 and j != 1:
            return model.order[j] >= model.order[i] + 1 - num_cities * (1 - model.x[(i, j)])
        return pyo.Constraint.Skip

    model.mtz = pyo.Constraint(model.cities, model.cities, rule=mtz_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}