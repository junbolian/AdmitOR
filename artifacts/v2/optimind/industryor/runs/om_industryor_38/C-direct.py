import gurobipy as gp
from gurobipy import GRB

def solve(params):
    price_steel = params["price_steel"]
    price_engines = params["price_engines"]
    price_electronics = params["price_electronics"]
    price_plastic = params["price_plastic"]

    steel_req_engines = params["steel_req_engines"]
    steel_req_plastic = params["steel_req_plastic"]
    steel_import_cost = params["steel_import_cost"]
    steel_labor = params["steel_labor"]

    engines_req_steel = params["engines_req_steel"]
    engines_req_electronics = params["engines_req_electronics"]
    engines_req_plastic = params["engines_req_plastic"]
    engines_import_cost = params["engines_import_cost"]
    engines_labor = params["engines_labor"]

    electronics_req_steel = params["electronics_req_steel"]
    electronics_req_engines = params["electronics_req_engines"]
    electronics_req_plastic = params["electronics_req_plastic"]
    electronics_import_cost = params["electronics_import_cost"]
    electronics_labor = params["electronics_labor"]

    plastic_req_engines = params["plastic_req_engines"]
    plastic_req_steel = params["plastic_req_steel"]
    plastic_req_electronics = params["plastic_req_electronics"]
    plastic_import_cost = params["plastic_import_cost"]
    plastic_labor = params["plastic_labor"]

    cap_engines = params["cap_engines"]
    cap_plastic = params["cap_plastic"]
    labor_available = params["labor_available"]

    model = gp.Model("Carelland_GDP")
    model.setParam("OutputFlag", 0)

    # Decision variables: production quantities
    x_s = model.addVar(lb=0.0, name="steel")
    x_e = model.addVar(lb=0.0, name="engines")
    x_c = model.addVar(lb=0.0, name="electronics")
    x_p = model.addVar(lb=0.0, name="plastic")

    # GDP = export revenue - import costs
    # Export revenue: price * production
    # Import costs: import_cost_per_unit * production (for each sector)
    revenue = (price_steel * x_s
               + price_engines * x_e
               + price_electronics * x_c
               + price_plastic * x_p)

    import_costs = (steel_import_cost * x_s
                    + engines_import_cost * x_e
                    + electronics_import_cost * x_c
                    + plastic_import_cost * x_p)

    model.setObjective(revenue - import_costs, GRB.MAXIMIZE)

    # Material balance constraints:
    # Each commodity produced must have enough net supply to cover internal demand.
    # Net production of commodity >= 0, i.e. production >= internal consumption.
    #
    # Steel: x_s >= engines_req_steel*x_e + electronics_req_steel*x_c + plastic_req_steel*x_p + steel_req_engines*x_s (wait - steel_req_engines is engines needed per steel, not steel needed per steel)
    #
    # Let's be careful:
    # steel_req_engines = engines required per unit of steel produced
    # So steel production consumes: steel_req_engines*x_s engines, steel_req_plastic*x_s plastic
    # engines production consumes: engines_req_steel*x_e steel, engines_req_electronics*x_e electronics, engines_req_plastic*x_e plastic
    # electronics production consumes: electronics_req_steel*x_c steel, electronics_req_engines*x_c engines, electronics_req_plastic*x_c plastic
    # plastic production consumes: plastic_req_engines*x_p engines, plastic_req_steel*x_p steel, plastic_req_electronics*x_p electronics
    #
    # Balance: production of each good >= total internal consumption of that good
    # Steel balance: x_s >= engines_req_steel*x_e + electronics_req_steel*x_c + plastic_req_steel*x_p
    # (steel produced by steel sector not consumed internally - steel is an output, not an input to itself)
    # Note: steel_req_engines means "engines required per unit of steel" - steel sector consumes engines, not steel itself.

    # Steel balance: steel produced >= steel consumed by other sectors
    model.addConstr(
        x_s >= engines_req_steel * x_e + electronics_req_steel * x_c + plastic_req_steel * x_p,
        name="steel_balance"
    )

    # Engines balance: engines produced >= engines consumed by other sectors
    model.addConstr(
        x_e >= steel_req_engines * x_s + electronics_req_engines * x_c + plastic_req_engines * x_p,
        name="engines_balance"
    )

    # Electronics balance: electronics produced >= electronics consumed by other sectors
    model.addConstr(
        x_c >= engines_req_electronics * x_e + electronics_req_plastic * x_p + plastic_req_electronics * x_p,
        name="electronics_balance"
    )

    # Plastic balance: plastic produced >= plastic consumed by other sectors
    model.addConstr(
        x_p >= steel_req_plastic * x_s + engines_req_plastic * x_e + electronics_req_plastic * x_c,
        name="plastic_balance"
    )

    # Capacity constraints
    model.addConstr(x_e <= cap_engines, name="cap_engines")
    model.addConstr(x_p <= cap_plastic, name="cap_plastic")

    # Labor constraint
    model.addConstr(
        steel_labor * x_s + engines_labor * x_e + electronics_labor * x_c + plastic_labor * x_p <= labor_available,
        name="labor"
    )

    model.optimize()

    status = model.Status
    if status == GRB.OPTIMAL:
        return {"objective": model.ObjVal, "status": "optimal"}
    elif status == GRB.INFEASIBLE:
        return {"objective": None, "status": "infeasible"}
    elif status == GRB.UNBOUNDED:
        return {"objective": None, "status": "unbounded"}
    else:
        return {"objective": None, "status": f"solver_status_{status}"}