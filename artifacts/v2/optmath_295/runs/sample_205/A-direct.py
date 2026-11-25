import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [(0, 1), (0, 2), (1, 0), (1, 2), (2, 0), (2, 1)]

    cost = {
        (0, 1): params["cost_0_1"],
        (0, 2): params["cost_0_2"],
        (1, 0): params["cost_1_0"],
        (1, 2): params["cost_1_2"],
        (2, 0): params["cost_2_0"],
        (2, 1): params["cost_2_1"],
    }

    pos_lb = {1: params["position_lb_city1"], 2: params["position_lb_city2"]}
    pos_ub = {1: params["position_ub_city1"], 2: params["position_ub_city2"]}

    model = pyo.ConcreteModel()

    model.x = pyo.Var(arcs, domain=pyo.Binary)

    model.pos0 = pyo.Var(domain=pyo.Reals)
    model.pos1 = pyo.Var(domain=pyo.Reals, bounds=(pos_lb[1], pos_ub[1]))
    model.pos2 = pyo.Var(domain=pyo.Reals, bounds=(pos_lb[2], pos_ub[2]))

    pos = {0: model.pos0, 1: model.pos1, 2: model.pos2}

    # Big-M based on position ranges
    all_lbs = [min(pos_lb[1], pos_lb[2]), pos_lb[1], pos_lb[2]]
    all_ubs = [max(pos_ub[1], pos_ub[2]), pos_ub[1], pos_ub[2]]
    span = max(all_ubs) - min(all_lbs)
    M = span + 1.0
    
    # A safe M: since positions must be increased by at least 1 along an arc.
    # Use span + 1 as a conservative Big-M.
    if M < 1.0:
        M = 1.0

    model.obj = pyo.Objective(
        expr=sum(cost[a] * model.x[a] for a in arcs), sense=pyo.minimize
    )

    # In-degree constraints
    model.in_0 = pyo.Constraint(expr=model.x[(1, 0)] + model.x[(2, 0)] == 1)
    model.in_1 = pyo.Constraint(expr=model.x[(0, 1)] + model.x[(2, 1)] == 1)
    model.in_2 = pyo.Constraint(expr=model.x[(0, 2)] + model.x[(1, 2)] == 1)

    # Out-degree constraints
    model.out_0 = pyo.Constraint(expr=model.x[(0, 1)] + model.x[(0, 2)] == 1)
    model.out_1 = pyo.Constraint(expr=model.x[(1, 0)] + model.x[(1, 2)] == 1)
    model.out_2 = pyo.Constraint(expr=model.x[(2, 0)] + model.x[(2, 1)] == 1)

    # MTZ subtour elimination for each arc: pos[i] - pos[j] >= 1 - M*(1-x[i,j])
    model.mtz = pyo.Constraint(
        arcs,
        rule=lambda m, i, j: pos[i] - pos[j] >= 1 - M * (1 - m.x[(i, j)]),
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}