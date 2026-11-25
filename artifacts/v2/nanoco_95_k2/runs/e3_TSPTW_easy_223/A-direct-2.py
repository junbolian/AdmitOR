import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    n = 8
    nodes = list(range(n))
    customers = list(range(1, n))

    TT = params["travel_time"]
    st = params["service_time"]
    M = params["max_shelf_life_window"]

    earliest = [params["tw_%d_earliest" % i] for i in nodes]
    latest = [params["tw_%d_latest" % i] for i in nodes]

    model = pyo.ConcreteModel()

    model.nodes = pyo.Set(initialize=nodes)
    model.customers = pyo.Set(initialize=customers)

    model.x = pyo.Var(model.nodes, model.nodes, domain=pyo.Binary)
    model.t = pyo.Var(model.nodes, domain=pyo.NonNegativeReals)

    def in_rule(md, j):
        return sum(md.x[i, j] for i in md.nodes if i != j) == 1
    model.in_con = pyo.Constraint(model.customers, rule=in_rule)

    def out_rule(md, i):
        return sum(md.x[i, j] for j in md.nodes if j != i) == 1
    model.out_con = pyo.Constraint(model.customers, rule=out_rule)

    model.depot_out = pyo.Constraint(
        expr=sum(model.x[0, j] for j in nodes if j != 0) == 1)
    model.depot_in = pyo.Constraint(
        expr=sum(model.x[i, 0] for i in nodes if i != 0) == 1)

    def self_rule(md, i, j):
        if i == j:
            return md.x[i, j] == 0
        return pyo.Constraint.Skip
    model.self_con = pyo.Constraint(model.nodes, model.nodes, rule=self_rule)

    # time window for customers
    def tw_rule(md, i):
        return (earliest[i], md.t[i], latest[i])
    model.tw_con = pyo.Constraint(model.customers, rule=tw_rule)

    # depot: departure time within [earliest0, latest0]
    model.depot_tw = pyo.Constraint(
        expr=(earliest[0], model.t[0], latest[0]))

    # Big-M
    BigM = max(latest) + max(
        TT[i][j] for i in nodes for j in nodes) + sum(
        st for _ in nodes) + 1000

    # MTZ-style time propagation for customers (no return-to-depot constraint here)
    def time_rule(md, i, j):
        if i == j:
            return pyo.Constraint.Skip
        return md.t[j] >= md.t[i] + st + TT[i][j] - BigM * (1 - md.x[i, j])
    model.time_con = pyo.Constraint(
        [i for i in nodes], [j for j in nodes], rule=time_rule)

    # total route duration: return time to depot = service start at 0 +
    # time to return. Model return arc and bound it.
    # Add a variable for the return-arrival time at depot.
    model.t_ret = pyo.Var(domain=pyo.NonNegativeReals)

    def ret_rule(md, i):
        if i == 0:
            return pyo.Constraint.Skip
        return md.t_ret >= md.t[i] + st + TT[i][0] - BigM * (1 - md.x[i, 0])
    model.ret_con = pyo.Constraint(model.nodes, rule=ret_rule)

    model.route_dur = pyo.Constraint(expr=model.t_ret <= M)

    model.total_cost = pyo.Objective(
        expr=sum(TT[i][j] * model.x[i, j]
                 for i in nodes for j in nodes if i != j),
        sense=pyo.minimize)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}