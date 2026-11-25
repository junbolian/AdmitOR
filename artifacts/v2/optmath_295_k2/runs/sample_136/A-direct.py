import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    nodes = list(range(7))
    arcs = [(i, j) for i in nodes for j in nodes if i != j]

    model = pyo.ConcreteModel()

    model.ARCS = pyo.Set(initialize=arcs, dimen=2)

    def cost_init(model_obj, i, j):
        return params["cost_{0}_{1}".format(i, j)]

    model.cost = pyo.Param(model.ARCS, initialize=cost_init)

    model.flow = pyo.Var(model.ARCS, domain=pyo.Binary)

    def obj_rule(model_obj):
        return pyo.quicksum(
            model_obj.cost[i, j] * model_obj.flow[i, j] for (i, j) in model_obj.ARCS
        )

    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Node 0: sent - received == supply_node_0
    def balance_0_rule(model_obj):
        sent = pyo.quicksum(model_obj.flow[0, j] for j in nodes if j != 0)
        received = pyo.quicksum(model_obj.flow[i, 0] for i in nodes if i != 0)
        return sent - received == params["supply_node_0"]

    model.balance_0 = pyo.Constraint(rule=balance_0_rule)

    # Node 6: received - sent == demand_node_6
    def balance_6_rule(model_obj):
        received = pyo.quicksum(model_obj.flow[i, 6] for i in nodes if i != 6)
        sent = pyo.quicksum(model_obj.flow[6, j] for j in nodes if j != 6)
        return received - sent == params["demand_node_6"]

    model.balance_6 = pyo.Constraint(rule=balance_6_rule)

    # Intermediate nodes: received - sent == balance_nodes_1_to_5
    def balance_inter_rule(model_obj, k):
        received = pyo.quicksum(model_obj.flow[i, k] for i in nodes if i != k)
        sent = pyo.quicksum(model_obj.flow[k, j] for j in nodes if j != k)
        return received - sent == params["balance_nodes_1_to_5"]

    model.BAL_NODES = pyo.Set(initialize=[1, 2, 3, 4, 5])
    model.balance_inter = pyo.Constraint(model.BAL_NODES, rule=balance_inter_rule)

    solver = Highs()
    solver.solve(model)

    try:
        obj_val = float(pyo.value(model.total_cost))
    except Exception:
        return {"objective": None, "status": "infeasible"}

    return {"objective": obj_val, "status": "optimal"}