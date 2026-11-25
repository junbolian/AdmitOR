import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = [0, 1, 2, 3, 4]
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    # Net outflow: positive means demand (outflow), negative means supply (inflow)
    # Hub 0: demand 147, Hub 1: demand 103, Hub 2: 0, Hub 3: supply 205, Hub 4: supply 45
    net_outflow = {
        0: params["net_outflow_demand_hub0"],
        1: params["net_outflow_demand_hub1"],
        2: 0.0,
        3: -params["net_inflow_supply_hub3"],
        4: -params["net_inflow_supply_hub4"],
    }

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)
    model.NODES = pyo.Set(initialize=nodes)

    # Binary: 1 if connection established
    model.y = pyo.Var(model.ARCS, domain=pyo.Binary)

    # Continuous flow on each arc
    model.flow = pyo.Var(model.ARCS, domain=pyo.NonNegativeReals)

    # Capacity: flow <= capacity * y
    def capacity_rule(m, i, j):
        cap = params["capacity_{}_{}".format(i, j)]
        return m.flow[i, j] <= cap * m.y[i, j]

    model.capacity_con = pyo.Constraint(model.ARCS, rule=capacity_rule)

    # Flow balance at each node
    def balance_rule(m, n):
        inflow = sum(m.flow[i, n] for i in nodes if i != n)
        outflow = sum(m.flow[n, j] for j in nodes if j != n)
        return outflow - inflow == net_outflow[n]

    model.balance_con = pyo.Constraint(model.NODES, rule=balance_rule)

    # Objective: fixed costs + variable costs
    def obj_rule(m):
        fixed = sum(
            params["fixed_cost_{}_{}".format(i, j)] * m.y[i, j]
            for (i, j) in m.ARCS
        )
        variable = sum(
            params["variable_cost_{}_{}".format(i, j)] * m.flow[i, j]
            for (i, j) in m.ARCS
        )
        return fixed + variable

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}