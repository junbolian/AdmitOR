import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    locations = [1, 2, 3, 4, 5, 6]

    # Build cost dictionary from params
    cost = {}
    for i in locations:
        for j in locations:
            if i != j:
                cost[(i, j)] = params["cost_{}_{}".format(i, j)]

    arcs = [(i, j) for i in locations for j in locations if i != j]

    model = pyo.ConcreteModel()

    model.L = pyo.Set(initialize=locations)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    model.cost = pyo.Param(model.A, initialize=cost)

    model.x = pyo.Var(model.A, domain=pyo.Binary)

    # Objective: minimize total travel cost
    def obj_rule(mod):
        return sum(mod.cost[i, j] * mod.x[i, j] for (i, j) in mod.A)

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Each location has exactly one outgoing arc
    def out_rule(mod, i):
        return sum(mod.x[i, j] for j in mod.L if j != i) == 1

    model.out_cons = pyo.Constraint(model.L, rule=out_rule)

    # Each location has exactly one incoming arc
    def in_rule(mod, j):
        return sum(mod.x[i, j] for i in mod.L if i != j) == 1

    model.in_cons = pyo.Constraint(model.L, rule=in_rule)

    # Subtour elimination (MTZ) with continuous order variables
    model.u = pyo.Var(model.L, domain=pyo.NonNegativeReals, bounds=(0, len(locations)))
    model.u[1].setlb(1)
    model.u[1].setub(1)

    for i in locations:
        for j in locations:
            if i != 1 and i != j and j != 1:
                model.add_component(
                    "mtz_%d_%d" % (i, j),
                    pyo.Constraint(
                        expr=model.u[i] - model.u[j] + len(locations) * model.x[i, j]
                        <= len(locations) - 1
                    ),
                )

    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}