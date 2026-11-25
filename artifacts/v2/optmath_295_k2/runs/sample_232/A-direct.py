import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    node_list = [0, 1, 2, 3]
    arc_list = [(i, j) for i in node_list for j in node_list if i != j]

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arc_list, dimen=2)
    model.NODES = pyo.Set(initialize=node_list)

    model.fixed_cost = pyo.Param(
        model.ARCS,
        initialize={(i, j): params[f"fixed_cost_{i}_{j}"] for (i, j) in arc_list},
        within=pyo.Reals,
    )
    model.variable_cost = pyo.Param(
        model.ARCS,
        initialize={(i, j): params[f"variable_cost_{i}_{j}"] for (i, j) in arc_list},
        within=pyo.Reals,
    )
    model.capacity = pyo.Param(
        model.ARCS,
        initialize={(i, j): params[f"capacity_{i}_{j}"] for (i, j) in arc_list},
        within=pyo.NonNegativeReals,
    )
    model.net_outflow = pyo.Param(
        model.NODES,
        initialize={i: params[f"net_outflow_node{i}"] for i in node_list},
        within=pyo.Reals,
    )

    model.flow = pyo.Var(model.ARCS, within=pyo.NonNegativeReals)
    model.open_arc = pyo.Var(model.ARCS, within=pyo.Binary)

    def flow_cap_rule(m, i, j):
        return m.flow[i, j] <= m.capacity[i, j] * m.open_arc[i, j]

    model.flow_cap = pyo.Constraint(model.ARCS, rule=flow_cap_rule)

    def balance_rule(m, i):
        outflow = sum(m.flow[i, j] for j in node_list if j != i)
        inflow = sum(m.flow[j, i] for j in node_list if j != i)
        return outflow - inflow == m.net_outflow[i]

    model.balance = pyo.Constraint(model.NODES, rule=balance_rule)

    def obj_rule(m):
        return sum(
            m.fixed_cost[i, j] * m.open_arc[i, j]
            + m.variable_cost[i, j] * m.flow[i, j]
            for (i, j) in arc_list
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}