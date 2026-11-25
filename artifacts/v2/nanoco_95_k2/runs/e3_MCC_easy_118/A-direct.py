import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    arcs = [
        (0, 1), (0, 2), (0, 5),
        (1, 0), (1, 2),
        (2, 0), (2, 1), (2, 3),
        (3, 2), (3, 4),
        (4, 1), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 3), (5, 4),
    ]

    unit_cost = params["unit_cost"]
    min_flow = params["min_flow"]
    capacity = params["capacity"]
    num_nodes = int(params["num_nodes"])
    num_pipes = int(params["num_pipes"])

    model = pyo.ConcreteModel()

    model.PIPES = pyo.RangeSet(0, num_pipes - 1)
    model.NODES = pyo.RangeSet(0, num_nodes - 1)

    cost_map = {arcs[i]: float(unit_cost[i]) for i in range(num_pipes)}
    lb_map = {arcs[i]: float(min_flow[i]) for i in range(num_pipes)}
    ub_map = {arcs[i]: float(capacity[i]) for i in range(num_pipes)}

    def flow_bounds(m, i):
        arc = arcs[i]
        return (lb_map[arc], ub_map[arc])

    model.flow = pyo.Var(model.PIPES, bounds=flow_bounds)

    def cost_rule(m):
        return sum(cost_map[arcs[i]] * m.flow[i] for i in m.PIPES)

    model.total_cost = pyo.Objective(rule=cost_rule, sense=pyo.minimize)

    def balance_rule(m, n):
        outflow = sum(m.flow[i] for i in m.PIPES if arcs[i][0] == n)
        inflow = sum(m.flow[i] for i in m.PIPES if arcs[i][1] == n)
        return outflow - inflow == 0

    model.balance = pyo.Constraint(model.NODES, rule=balance_rule)

    Highs().solve(model)

    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}