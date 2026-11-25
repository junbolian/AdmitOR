import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # Structural constants: ordered pipe list
    pipe_list = [
        (0, 1), (0, 2), (0, 5),
        (1, 0), (1, 2),
        (2, 0), (2, 1), (2, 3),
        (3, 2), (3, 4),
        (4, 1), (4, 2), (4, 3), (4, 5),
        (5, 0), (5, 3), (5, 4),
    ]
    num_nodes = int(params["num_nodes"])

    cost = params["unit_cost"]
    min_flow = params["min_flow"]
    cap = params["capacity"]

    model = pyo.ConcreteModel()

    model.PIPES = pyo.Set(initialize=range(len(pipe_list)), ordered=True)
    model.NODES = pyo.Set(initialize=range(num_nodes), ordered=True)

    model.flow = pyo.Var(model.PIPES, domain=pyo.NonNegativeReals)

    lo = {i: min_flow[i] for i in range(len(pipe_list))}
    hi = {i: cap[i] for i in range(len(pipe_list))}
    model.flow_lo = pyo.Constraint(model.PIPES, rule=lambda model, i: model.flow[i] >= lo[i])
    model.flow_hi = pyo.Constraint(model.PIPES, rule=lambda model, i: model.flow[i] <= hi[i])

    # Node balance: total inflow == total outflow
    def balance_rule(model, n):
        inflow = sum(model.flow[i] for i, (a, b) in enumerate(pipe_list) if b == n)
        outflow = sum(model.flow[i] for i, (a, b) in enumerate(pipe_list) if a == n)
        return inflow == outflow

    model.balance = pyo.Constraint(model.NODES, rule=balance_rule)

    model.total_cost = pyo.Objective(
        expr=sum(cost[i] * model.flow[i] for i in model.PIPES),
        sense=pyo.minimize,
    )

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}