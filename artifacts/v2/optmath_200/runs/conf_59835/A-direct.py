import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 6
    supply_demand = params["supply_demand"]
    cost_matrix = params["cost_matrix"]
    capacity_matrix = params["capacity_matrix"]

    # Build ordered list of all directed arcs (i -> j), i != j
    # Ordering matches the given cost_matrix / capacity_matrix ordering.
    arcs = []
    for i in range(n):
        for j in range(n):
            if i != j:
                arcs.append((i, j))

    cost = {}
    cap = {}
    for k, (i, j) in enumerate(arcs):
        cost[(i, j)] = cost_matrix[k]
        cap[(i, j)] = capacity_matrix[k]

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    # Capacity constraints
    model.capacity_con = pyo.Constraint(
        model.ARCS,
        rule=lambda m, i, j: m.flow[(i, j)] <= cap[(i, j)],
    )

    # Flow balance: outflow - inflow = supply_demand at each city
    def balance_rule(m, c):
        outflow = sum(m.flow[(c, j)] for j in range(n) if j != c)
        inflow = sum(m.flow[(i, c)] for i in range(n) if i != c)
        return outflow - inflow == supply_demand[c]

    model.balance_con = pyo.Constraint(range(n), rule=balance_rule)

    # Objective: minimize total transportation cost
    model.total_cost = pyo.Objective(
        expr=sum(cost[(i, j)] * model.flow[(i, j)] for (i, j) in arcs),
        sense=pyo.minimize,
    )

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}