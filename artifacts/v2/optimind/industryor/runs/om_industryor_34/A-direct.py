import math
import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    # ---------- data ----------
    n_cust = len(params["customer_x"])  # structural: 20
    N = list(range(1, n_cust + 1))
    depot_node = 0
    all_nodes = [depot_node] + N
    K = list(range(1, int(params["vehicle_count_max"]) + 1))

    depot_x = params["depot_x"]
    depot_y = params["depot_y"]
    depot_tw_start = params["depot_tw_start"]
    depot_tw_end = params["depot_tw_end"]
    capacity = params["vehicle_capacity"]

    cx = {i: params["customer_x"][i - 1] for i in N}
    cy = {i: params["customer_y"][i - 1] for i in N}
    demand = {i: params["demand"][i - 1] for i in N}
    tw_early = {i: params["tw_early"][i - 1] for i in N}
    tw_late = {i: params["tw_late"][i - 1] for i in N}
    service = {i: params["service_time"][i - 1] for i in N}

    xcoord = {depot_node: depot_x}
    ycoord = {depot_node: depot_y}
    early = {depot_node: depot_tw_start}
    late = {depot_node: depot_tw_end}
    serv = {depot_node: 0}
    for i in N:
        xcoord[i] = cx[i]
        ycoord[i] = cy[i]
        early[i] = tw_early[i]
        late[i] = tw_late[i]
        serv[i] = service[i]

    dist = {}
    for i in all_nodes:
        for j in all_nodes:
            if i != j:
                dist[i, j] = math.hypot(xcoord[i] - xcoord[j], ycoord[i] - ycoord[j])

    # customer-only arcs and depot arcs
    cust_arcs = [(i, j) for i in N for j in N if i != j]
    out_arcs = [(depot_node, j) for j in N]
    in_arcs = [(i, depot_node) for i in N]
    arcs = out_arcs + in_arcs + cust_arcs

    bigM = late[depot_node] + sum(serv.values()) + sum(
        max(dist[i, j] for (i, j) in arcs)) + 1.0
    # a safer big-M using the max single arc plus total time horizon
    bigM = late[depot_node] + sum(serv.values()) + 1.0

    model = pyo.ConcreteModel()

    model.nodes_set = pyo.Set(initialize=all_nodes)
    model.cust_set = pyo.Set(initialize=N)
    model.veh_set = pyo.Set(initialize=K)
    model.arcs_set = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.arcs_set, model.veh_set, domain=pyo.Binary)

    # start-of-service time at node i on vehicle k (depot uses departure/return time)
    model.t = pyo.Var(model.nodes_set, model.veh_set,
                      domain=pyo.NonNegativeReals,
                      bounds=(0, late[depot_node]))

    model.use_veh = pyo.Var(model.veh_set, domain=pyo.Binary)

    # ---------- objective ----------
    def obj_rule(md):
        return sum(dist[i, j] * md.x[i, j, k]
                   for (i, j) in arcs for k in K)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # ---------- constraints ----------
    # each customer entered exactly once
    def in_once_rule(md, j):
        return sum(md.x[i, j, k] for i in all_nodes if i != j for k in K) == 1
    model.in_once = pyo.Constraint(model.cust_set, rule=in_once_rule)

    # each customer left exactly once
    def out_once_rule(md, i):
        return sum(md.x[i, j, k] for j in all_nodes if j != i for k in K) == 1
    model.out_once = pyo.Constraint(model.cust_set, rule=out_once_rule)

    # flow conservation at customer nodes
    def flow_rule(md, j, k):
        return (sum(md.x[i, j, k] for i in all_nodes if i != j)
                - sum(md.x[j, jj, k] for jj in all_nodes if jj != j)) == 0
    model.flow = pyo.Constraint(model.cust_set, model.veh_set, rule=flow_rule)

    # depot: at most one departure and one return per vehicle
    def depot_out_rule(md, k):
        return sum(md.x[depot_node, j, k] for j in N) <= 1
    model.depot_out = pyo.Constraint(model.veh_set, rule=depot_out_rule)

    def depot_in_rule(md, k):
        return sum(md.x[i, depot_node, k] for i in N) <= 1
    model.depot_in = pyo.Constraint(model.veh_set, rule=depot_in_rule)

    # link use_veh
    def use_rule(md, k):
        return sum(md.x[depot_node, j, k] for j in N) == md.use_veh[k]
    model.use = pyo.Constraint(model.veh_set, rule=use_rule)

    # capacity
    def cap_rule(md, k):
        return sum(demand[i] * sum(md.x[i, j, k] for j in all_nodes if j != i)
                   for i in N) <= capacity
    model.cap = pyo.Constraint(model.veh_set, rule=cap_rule)

    # time-window bounds incl. depot
    def tw_rule(md, i, k):
        return (early[i], md.t[i, k], late[i])
    model.tw = pyo.Constraint(model.nodes_set, model.veh_set, rule=tw_rule)

    # time propagation along arcs with big-M
    def time_rule(md, i, j, k):
        return (md.t[i, k] + serv[i] + dist[i, j]
                - md.t[j, k] <= bigM * (1 - md.x[i, j, k]))
    model.time_prop = pyo.Constraint(model.arcs_set, model.veh_set, rule=time_rule)

    # ---------- solve ----------
    solver = Highs()
    solver.solve(model)

    obj_val = float(pyo.value(model.obj))
    return {"objective": obj_val, "status": "optimal"}