import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    N = 4

    cost = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (0, 3): params["cost_0_3"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (1, 3): params["cost_1_3"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
        (2, 3): params["cost_2_3"],
        (3, 0): params["cost_3_0"],
        (3, 1): params["cost_3_1"],
        (3, 2): params["cost_3_2"],
    }

    model = pyo.ConcreteModel()

    arcs = [(i, j) for i in range(N) for j in range(N) if i != j]
    model.arcs = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.arcs, domain=pyo.Binary)

    # Position of each city in the sequence
    model.pos = pyo.Var(range(N), domain=pyo.NonNegativeReals)

    # City 0 fixed at position 0
    model.pos_con0 = pyo.Constraint(expr=model.pos[0] == params["city0_position"])

    lb = params["position_lower_bound"]
    ub = params["position_upper_bound"]
    for c in [1, 2, 3]:
        model.add_component(
            "pos_lb_%d" % c,
            pyo.Constraint(expr=model.pos[c] >= lb),
        )
        model.add_component(
            "pos_ub_%d" % c,
            pyo.Constraint(expr=model.pos[c] <= ub),
        )

    # Each city has exactly one outgoing and one incoming route
    def out_rule(mdl, i):
        return sum(mdl.x[i, j] for j in range(N) if j != i) == 1

    def in_rule(mdl, j):
        return sum(mdl.x[i, j] for i in range(N) if i != j) == 1

    model.out_con = pyo.Constraint(range(N), rule=out_rule)
    model.in_con = pyo.Constraint(range(N), rule=in_rule)

    # MTZ-style subtour elimination with strict ordering
    bigM = params["position_upper_bound"] + 1

    def order_rule(mdl, i, j):
        if i == 0 or j == 0:
            return pyo.Constraint.Skip
        return mdl.pos[i] + 1 <= mdl.pos[j] + bigM * (1 - mdl.x[i, j])

    model.order_con = pyo.Constraint(model.arcs, rule=order_rule)

    model.obj = pyo.Objective(
        expr=sum(cost[i, j] * model.x[i, j] for (i, j) in model.arcs),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}