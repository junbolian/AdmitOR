import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    shipping_cost = params["shipping_cost"]
    fixed_cost_dc = params["fixed_cost_dc"]
    throughput_cost = params["throughput_cost"]
    plant_supply = params["plant_supply"]
    demand = params["demand"]
    dc_min = params["dc_min_throughput"]
    dc_max = params["dc_max_throughput"]

    commodities = [0, 1, 2]
    plants = [0, 1]
    dcs = [0, 1]
    zones = [0, 1, 2, 3]

    model = pyo.ConcreteModel()

    model.C = pyo.Set(initialize=commodities)
    model.P = pyo.Set(initialize=plants)
    model.D = pyo.Set(initialize=dcs)
    model.Z = pyo.Set(initialize=zones)

    # shipping quantity: plant p ships commodity c to DC d for zone z
    model.x = pyo.Var(model.P, model.D, model.Z, model.C, within=pyo.NonNegativeReals)

    # DC selection binary
    model.y = pyo.Var(model.D, within=pyo.Binary)

    # zone assignment binary: zone z assigned to DC d
    model.w = pyo.Var(model.Z, model.D, within=pyo.Binary)

    # total flow into each DC (for throughput costs and bounds)
    def dc_total_flow_rule(model, d):
        return sum(model.x[p, d, z, c]
                   for p in model.P for z in model.Z for c in model.C)
    model.dc_flow = pyo.Expression(model.D, rule=dc_total_flow_rule)

    # Objective
    def obj_rule(model):
        shipping = sum(shipping_cost[p][d][z][c] * model.x[p, d, z, c]
                       for p in model.P for d in model.D
                       for z in model.Z for c in model.C)
        fixed = sum(fixed_cost_dc[d] * model.y[d] for d in model.D)
        throughput = sum(throughput_cost[d][z] * model.x[p, d, z, c]
                         for d in model.D for z in model.Z
                         for p in model.P for c in model.C)
        return shipping + fixed + throughput
    model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Demand satisfaction: shipments to assigned DC equal demand
    def demand_rule(model, z, c):
        return sum(model.x[p, d, z, c]
                   for p in model.P for d in model.D) >= demand[c][z]
    model.demand_con = pyo.Constraint(model.Z, model.C, rule=demand_rule)

    # Zone assigned to exactly one DC
    def assign_rule(model, z):
        return sum(model.w[z, d] for d in model.D) == 1
    model.assign_con = pyo.Constraint(model.Z, rule=assign_rule)

    # Only ship to DC for a zone if zone assigned to that DC
    def link_rule(model, p, d, z, c):
        return model.x[p, d, z, c] <= 10000 * model.w[z, d]
    model.link_con = pyo.Constraint(model.P, model.D, model.Z, model.C, rule=link_rule)

    # Throughput min/max linked to selection
    def thru_min_rule(model, d):
        return model.dc_flow[d] >= dc_min[d] * model.y[d]
    model.thru_min_con = pyo.Constraint(model.D, rule=thru_min_rule)

    def thru_max_rule(model, d):
        return model.dc_flow[d] <= dc_max[d] * model.y[d]
    model.thru_max_con = pyo.Constraint(model.D, rule=thru_max_rule)

    # Plant supply capacity per commodity
    def supply_rule(model, p, c):
        return sum(model.x[p, d, z, c]
                   for d in model.D for z in model.Z) <= plant_supply[p][c]
    model.supply_con = pyo.Constraint(model.P, model.C, rule=supply_rule)

    Highs().solve(model)
    obj_val = float(pyo.value(model.total_cost))
    return {"objective": obj_val, "status": "optimal"}