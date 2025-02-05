import numpy as np
import pandas as pd
import plotly.express as px

# Define the parameters for the Global Budget based on temperature and probability of reaching this temperature 
# (IPCC. Summary for Policymakers: Climate Change 2021: The Physical Science Basis. Contribution
# of Working Group I to the Sixth Assessment Report of the Intergovernmental Panel on Climate Change)

global_budget = {
    (1.5, 17): 900, (1.5, 33): 650, (1.5, 50): 500, (1.5, 67): 400, (1.5, 83): 300,
    (1.7, 17): 1450, (1.7, 33): 1050, (1.7, 50): 850, (1.7, 67): 700, (1.7, 83): 550,
    (2.0, 17): 2300, (2.0, 33): 1700, (2.0, 50): 1350, (2.0, 67): 1150, (2.0, 83): 900
}

# Fn values for allocation of national budget
Fn_values = {
    'Equal per capita': 0.0106, # German population / World population
    'Grandfathering': 0.0179,   # Current German emissions / current World emissions
    'GDP proportional': 0.0407  # German GDP / World GDP
}

# Fb, Fe and Fo values for the shares of the building sector and within the building sector for operational and embodied emissions
Fb = 0.303  # Share of the building sector on national emissions in Germany
Fe = 0.3707 # Average share of embodied emissions on the emissions of the building sector (Yearly average from 2025 to 2045)
Fo = 1 - Fe # Average share of operational emissions on the emissions of the building sector (Yearly average from 2025 to 2045)

# Residential net room area in m²: First the residential living area minus residential areas in non-residential buildings 
# (already included in non-residential net room area) (Destatis (2024), Destatis (2024b)). Only data for the living area is 
# available that is why it needs to be multiplied with two factors to first calculate the gross floor area (1.87) and then
# deduct the construction area (0.83) (BKI Baukosten Gebäude Neubau (2024), p. 97, p.100) to get the net room area for 
# residential buildings in m²:

Ae_residential = (4024768000 - 127039000) * 1.87 * 0.83

# Non-residential net room area that is relevant to the German Building Energy Act (GEG) in m² from Hörner et al. (2024, https://doi.org/10.1016/j.buildenv.2024.111407):

Ae_nonresidential = 3073000000 

Ae_initial = Ae_residential + Ae_nonresidential # Total area of the German building stock that is relevant to the GEG

# Function to calculate both emissions based on user inputs
def calculate_emissions(GB, Fn, year_GHG_neutrality, rn, rr, rd):
    GB = GB - 185           # Budget reduction, deducting the emissions from 2020 to 2024
    GB_GHG = GB / 0.887     # Using the factor of 0.887 (Share of CO2 on German greenhouse gas (GHG) emissions) to get a GHG budget instead of CO2 budget.

    # Calculates building area and emissions per year from 2025 up to 'year_GHG_neutrality' (e.g., 2045).

    # Steps:
    # 1) Pre-correction for the period 2021–2025.
    # 2) Year-by-year calculation of:
    #   - Total building area
    #   - Newly added building area
    #   - Operational emissions
    #   - Embodied emissions

    # 1) Pre-correction for the period 2021–2025
    years_pre = 2025 - 2021  # Number of years before 2025 we want to account for
    Ae_temp = Ae_initial

    for _ in range(years_pre):
        # Estimate new construction and demolition in each of those pre-years
        pre_An = rn * Ae_temp  # New construction
        pre_Ad = rd * Ae_temp  # Demolition
        Ae_temp += pre_An - pre_Ad

    # Building area in 2025 (after pre-correction)
    Ae_2025 = Ae_temp
    
    # 2) Initialize lists to store yearly results
    years = list(range(2025, year_GHG_neutrality + 1))  # from 2025 to 'year_GHG_neutrality'
    Ae_list = []      # Total building area per year
    Anew_list = []    # Newly added (An + Ar) building area per year
    op_em_list = []   # Operational emissions per year
    emb_em_list = []  # Embodied emissions per year

    Ae_current = Ae_2025

    # Total budget for operational GHG emissions in Germany
    share_operational = GB_GHG * Fn * Fb * Fo * 1e12  # kg CO2e (instead of Gt)

    # Total budget for embodied GHG emissions in Germany 
    share_embodied = GB_GHG * Fn * Fb * Fe * 1e12  # kg CO2e (instead of Gt)

    for year in years:
        # Annual new construction, demolition, and renovation area
        An = rn * Ae_current
        Ad = rd * Ae_current
        Ar = rr * Ae_current

        # Update total building area for the next year
        Ae_current += An - Ad

        # Newly added area = new construction + renovation
        A_new = An + Ar

        # Operational emissions per year for the existing total building area per m²
        # Divided by 21 to spread over 2025–2045 (21 years, including 2025), as an example
        E_op = share_operational / (year_GHG_neutrality + 1 - 2025) / Ae_current  # kg CO2e per year and per m²

        # Embodied emissions per year  per m² (new construction + renovation) and distributed over a life-cycle of 50 years
        E_emb = share_embodied / (year_GHG_neutrality + 1 - 2025) / A_new / 50  # kg CO2e per year and per m²

        # Store values in the lists
        Ae_list.append(Ae_current)
        Anew_list.append(A_new)
        op_em_list.append(E_op)
        emb_em_list.append(E_emb)

    # Sum up emissions over the period 2025–2045
    total_op_em = sum(op_em_list)
    total_emb_em = sum(emb_em_list)
    # Calculate the average emissions per m² and per year
    average_op_em = total_op_em/(year_GHG_neutrality + 1 - 2025)
    average_emb_em = total_emb_em/(year_GHG_neutrality + 1 - 2025)

    return average_op_em, average_emb_em

# Prepare the data for all combinations of parameters
rows = []
for (temp_goal, prob), GB in global_budget.items():
    for fn_label, Fn in Fn_values.items():
        for year_GHG_neutrality in range(2035, 2051, 5):  # Year of climate neutrality from 2035 to 2050
            for rn in np.arange(0.005, 0.0151, 0.002):  # New build rate ranging from 0.5 % to 1.5 %
                for rr in np.arange(0.005, 0.0201, 0.0025):  # Renovation rate ranging from 0.5 % to 2 %
                    for rd in np.arange(0.0005, 0.0051, 0.0005):  # Demolition rate ranging from 0.05 % to 0.5 %
                        op_emissions, emb_emissions = calculate_emissions(GB, Fn, year_GHG_neutrality, rn, rr, rd)
                        rows.append([
                            temp_goal, prob, fn_label, Fn * 100, year_GHG_neutrality, rn * 100, rr * 100, rd * 100, op_emissions, emb_emissions
                        ])

# Create a DataFrame with the results
df = pd.DataFrame(rows, columns=[
    'Temp. Goal (°C)', 'Probability (%)', 'National Budget Allocation Label',
    'National Budget Allocation Value (%)', 'Year of Climate Neutrality',
    'New Build Rate', 'Renovation Rate', 'Demolition Rate',
    'Operational Emissions (kg CO2e/(m²·a))',
    'Embodied Emissions (kg CO2e/(m²·a))'
])

# Setting the color code
alpha = Fo  # Share for color coding
df['-'] = (alpha * df['Operational Emissions (kg CO2e/(m²·a))'] +
                         (1 - alpha) * df['Embodied Emissions (kg CO2e/(m²·a))'])

# Prepare tick values for percentage axes
tick_values_rn = [rn * 100 for rn in np.arange(0.005, 0.0151, 0.002)]
tick_values_rr = [rr * 100 for rr in np.arange(0.005, 0.0201, 0.0025)]
tick_values_rd = [rd * 100 for rd in np.arange(0.0005, 0.0051, 0.0005)]

# Plot the Parallel Coordinates Chart
fig = px.parallel_coordinates(
    df,
    dimensions=[
        "Temp. Goal (°C)", 
        "Probability (%)", 
        "National Budget Allocation Label",
        "National Budget Allocation Value (%)",
        "Year of Climate Neutrality",
        "New Build Rate",
        "Renovation Rate",
        "Demolition Rate", 
        "Operational Emissions (kg CO2e/(m²·a))", 
        "Embodied Emissions (kg CO2e/(m²·a))"     
    ],
    color="-",
    color_continuous_scale=px.colors.diverging.Tealrose,
    labels={
        "Temp. Goal (°C)": "Temp. Goal (°C)",
        "Probability (%)": "Probability (%)",
        "National Budget Allocation Label": "Budget Allocation",
        "National Budget Allocation Value (%)": "Allocation Value (%)",
        "Year of Climate Neutrality": "Climate Neutrality Year",
        "New Build Rate": "New Build Rate (%)",
        "Renovation Rate": "Renovation Rate (%)",
        "Demolition Rate": "Demolition Rate (%)",
        "Operational Emissions (kg CO2e/(m²·a))": "Operational Emissions",
        "Embodied Emissions (kg CO2e/(m²·a))": "Embodied Emissions"
    }
)

# Update tick values for axes
fig.update_traces(dimensions=[
    dict(label="", values=df["Temp. Goal (°C)"], tickvals=[1.5, 1.7, 2.0]),
    dict(label="", values=df["Probability (%)"], tickvals=[17, 33, 50, 67, 83]),
    dict(label="", values=df["National Budget Allocation Value (%)"], tickvals=[1.06, 1.79, 4.07]),
    dict(label="", values=df["Year of Climate Neutrality"], tickvals=[2035, 2040, 2045, 2050]),
    dict(label="", values=df["New Build Rate"], tickvals=tick_values_rn),
    dict(label="", values=df["Renovation Rate"], tickvals=tick_values_rr),
    dict(label="", values=df["Demolition Rate"], tickvals=tick_values_rd),
    dict(label="", values=df["Operational Emissions (kg CO2e/(m²·a))"], tickvals = [0.86, 3.86, 50, 100, 150, 184.4], ticktext = ["0.86", "3.86", "50", "100", "150", "184.4"]),
    dict(label="", values=df["Embodied Emissions (kg CO2e/(m²·a))"], tickvals = [0.29, 2.41, 50, 100, 150, 200, 217.25], ticktext= ["0.29", "2.41", "50", "100", "150", "200", "217.3"])
])


# Add custom annotations for axis titles
annotations = [
    dict(x=-0.034, y=1.09, showarrow=False, text="Temp. Goal<br>(°C)", xref="paper", yref="paper", font=dict(family="Arial", size=30)),
    dict(x=0.0935, y=1.09, showarrow=False, text="Probability<br>(%)", xref="paper", yref="paper", font=dict(family="Arial", size=30)),
    dict(x=0.185, y=1.09, showarrow=False, text="Nat. Allocation Value<br>(%)", xref="paper", yref="paper", font=dict(family="Arial", size=30)),
    dict(x=0.32, y=1.09, showarrow=False, text="Climate Neutrality<br>Year", xref="paper", yref="paper", font=dict(family="Arial", size=30)),
    dict(x=0.5, y=1.09, showarrow=False, text="New Build Rate<br>(%)", xref="paper", yref="paper", font=dict(family="Arial", size=30)),
    dict(x=0.625, y=1.09, showarrow=False, text="Renovation Rate<br>(%)", xref="paper", yref="paper", font=dict(family="Arial", size=30)),
    dict(x=0.8, y=1.09, showarrow=False, text="Demolition Rate<br>(%)", xref="paper", yref="paper", font=dict(family="Arial", size=30)),
    dict(x=0.92, y=1.09, showarrow=False, text="Op. Emissions<br>(kg CO2e/(m²·a))", xref="paper", yref="paper", font=dict(family="Arial", size=30)),
    dict(x=1.042, y=1.09, showarrow=False, text="Em. Emissions<br>(kg CO2e/(m²·a))", xref="paper", yref="paper", font=dict(family="Arial", size=30))
]

# Update annotations and adjust margins
fig.update_layout(
    annotations = annotations,
    font=dict(
        family="Arial",
        size = 40,
        color="black" 
    ),
    coloraxis_colorbar=dict(
        titlefont=dict(color="black"), 
        tickfont=dict(color="black"),
    ),
    margin=dict(l=100, r=100, t=100, b=100)
)

# Show the plot
fig.show()