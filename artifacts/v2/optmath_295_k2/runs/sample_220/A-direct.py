import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    demand_0 = params["demand_0"]
    demand_1 = params["demand_1"]
    supply_2 = params["supply_2"]
    supply_3 = params["supply_3"]
    supply_4 = params["supply_4"]

    fixed_cost_min = params["fixed_cost_min"]
    fixed_cost_max = params["fixed_cost_max"]
    variable_cost_min = params["variable_cost_min"]
    variable_cost_max = params["variable_cost_max"]
    capacity_min = params["capacity_min"]
    capacity_max = params["capacity_max"]

    nodes = [0, 1, 2, 3, 4]
    net_demand = {0: demand_0, 1: demand_1, 2: -supply_2, 3: -supply_3, 4: -supply_4}

    arcs = []
    for i in nodes:
        for j in nodes:
            if i != j:
                arcs.append((i, j))

    n_arcs = len(arcs)
    span = fixed_cost_max - fixed_cost_min
    fixed_cost = {}
    variable_cost = {}
    capacity = {}
    for idx, (i, j) in enumerate(arcs):
        f = (idx % 3) / 2.0
        g = ((idx * 7 + 1) % 3) / 2.0
        h = ((idx * 5 + 2) % 3) / 2.0
        fixed_cost[(i, j)] = fixed_cost_min + span * f
        variable_cost[(i, j)] = variable_cost_min + (variable_cost_max - variable_cost_min) * g
        capacity[(i, j)] = capacity_min + (capacity_max - capacity_min) * h

    model = pyo.ConcreteModel()
    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    model.f = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.ARCS, domain=pyo.Binary)

    model.capacity_con = pyo.Constraint(
        model.ARCS, rule=lambda m, i, j: m.f[i, j] <= capacity[(i, j)] * m.y[i, j]
    )

    def flow_balance(m, k):
        inflow = sum(m.f[i, k] for i in nodes if (i, k) in m.ARCS)
        outflow = sum(m.f[k, j] for j in nodes if (k, j) in m.ARCS)
        return inflow - outflow == net_demand[k]

    model.balance_con = pyo.Constraint(nodes, rule=flow_balance)

    model.total_cost = pyo.Objective(
        expr=sum(
            fixed_cost[(i, j)] * model.y[i, j] + variable_cost[(i, j)] * model.f[i, j]
            for (i, j) in model.ARCS
        ),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}