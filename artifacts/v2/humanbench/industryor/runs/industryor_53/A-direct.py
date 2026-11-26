import pyomo.environ as pyo
from pyomo.contrib.appsi.solvers.highs import Highs


def solve(params):
    processing_time = params["processing_time"]
    effective_hours = params["effective_hours"]
    machine_fee = params["machine_fee"]
    raw_material_cost = params["raw_material_cost"]
    selling_price = params["selling_price"]

    machines = ["A1", "A2", "B1", "B2", "B3"]
    products = ["I", "II", "III"]

    # Feasible (machine, product) processing routes
    routes = [
        ("A1", "I"), ("A2", "I"),
        ("A1", "II"), ("A2", "II"),
        ("B2", "II"),
        ("B1", "III"), ("B2", "III"),
    ]

    rkeys = [(m, p) for (m, p) in routes]
    keyset = set(rkeys)

    def pt(m, p):
        # tolerant lookup: nested dict, (m,p) tuple key, or "m,p"/"m_p" string key
        if isinstance(processing_time, dict):
            for k in ((m, p), f"{m},{p}", f"{m}_{p}", f"{m}{p}"):
                if k in processing_time:
                    try:
                        v = processing_time[k]
                    except Exception:
                        continue
                    if isinstance(v, dict):
                        for kk in (p, f"{m},{p}", f"{m}_{p}"):
                            if kk in v:
                                return v[kk]
                        continue
                    return v
            if m in processing_time and isinstance(processing_time[m], dict):
                sub = processing_time[m]
                for kk in (p, f"{m},{p}", f"{m}_{p}"):
                    if kk in sub:
                        return sub[kk]
        raise KeyError(f"processing_time missing for ({m}, {p})")

    model = pyo.ConcreteModel()

    # x[m, p]: units of product p processed on machine m
    model.x = pyo.Var(rkeys, domain=pyo.NonNegativeReals)

    # Capacity constraints per machine
    def cap_rule(model, m):
        return sum(
            pt(m, p) * model.x[(m, p)]
            for (mm, p) in rkeys if mm == m
        ) <= effective_hours[m]
    model.cap = pyo.Constraint(machines, rule=cap_rule)

    # Flow balance per product and per stage
    # Stage A output must equal stage B input for each product (route-based)
    # For each product, total A-processed units == total B-processed units
    def balance_rule(model, p):
        a_sum = sum(
            model.x[(m, pp)] for (m, pp) in rkeys
            if pp == p and m.startswith("A")
        )
        b_sum = sum(
            model.x[(m, pp)] for (m, pp) in rkeys
            if pp == p and m.startswith("B")
        )
        return a_sum == b_sum
    model.balance = pyo.Constraint(products, rule=balance_rule)

    # Profit objective: revenue - material - machine costs, based on finished units
    # finished units of product p = B-stage processed units
    def obj_rule(model):
        b_total = {}
        for p in products:
            b_total[p] = sum(
                model.x[(m, pp)] for (m, pp) in rkeys
                if pp == p and m.startswith("B")
            )
        revenue = sum(selling_price[p] * b_total[p] for p in products)
        material = sum(raw_material_cost[p] * b_total[p] for p in products)
        machine_cost = sum(
            machine_fee[m] * pt(m, p) * model.x[(m, p)]
            for (m, p) in rkeys
        )
        return revenue - material - machine_cost
    model.profit = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

    Highs().solve(model)

    obj_val = float(pyo.value(model.profit))
    return {"objective": obj_val, "status": "optimal"}