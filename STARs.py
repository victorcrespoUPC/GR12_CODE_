from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from main import (
    casos_presentacio,
    getCDO,
    NM_TO_KM
)


# Taula de referència de les STARs (Punt d'entrada, IAF i distància)
stars_list = {
    "ALBER1Z": {"entry_wp": "ALBER", "iaf": "CLE", "dist_nm": 69.7},
    "PUMAL1Z": {"entry_wp": "PUMAL", "iaf": "CLE", "dist_nm": 51.0},
    "MARTA3Z": {"entry_wp": "MARTA", "iaf": "RULOS", "dist_nm": 96.3},
    "MATEX3Z": {"entry_wp": "MATEX", "iaf": "RULOS", "dist_nm": 102.6},
    "LOBAR2W": {"entry_wp": "LOBAR", "iaf": "SLL", "dist_nm": 81.7},
    "CASPE2W": {"entry_wp": "CASPE", "iaf": "SLL", "dist_nm": 78.6},
}

flights_scenario_1 = [
    {"ac_model": "B767-300ER", "star": "ALBER1Z", "pct_mlw": 80.0},
    {"ac_model": "B737", "star": "PUMAL1Z", "pct_mlw": 100.0},
    {"ac_model": "B777-300", "star": "MARTA3Z", "pct_mlw": 100.0},
    {"ac_model": "B767-300ER", "star": "MATEX3Z", "pct_mlw": 80.0},
    {"ac_model": "A319-131", "star": "LOBAR2W", "pct_mlw": 80.0},
    {"ac_model": "A320-212", "star": "CASPE2W", "pct_mlw": 100.0},
]

for star, info in stars_list.items():
    info["dist_km"] = info["dist_nm"] * NM_TO_KM

ENTRY_TIME = datetime.strptime("11:45:00", "%H:%M:%S")


def compute_scenario_1():
    results = []

    for flight in flights_scenario_1:
        model = flight["ac_model"]
        star_id = flight["star"]
        pct_mlw = flight["pct_mlw"]

        star_data = stars_list[star_id]
        dist_iaf_m = star_data["dist_km"] * 1000.0

        # Trajectòria CDO backward (x_traj surt de 0 a valors negatius)
        x_traj, h_traj, v_traj = getCDO(model, pct_mlw)

        # MÈTODE 2: Recorrem la simulació fins a assolir la distància de la STAR
        # Com que dt = 1 s a cada iteració, l'índex i és directament el temps en segons
        alt_entry_m = h_traj[-1]
        time_to_iaf_s = float(len(x_traj) - 1)

        for i in range(len(x_traj)):
            if (x_traj[i]) >= dist_iaf_m:
                alt_entry_m = h_traj[i]
                time_to_iaf_s = float(i)
                break

        # Hora d'arribada (TOA) a l'IAF
        toa_iaf = ENTRY_TIME + timedelta(seconds=time_to_iaf_s)

        results.append(
            {
                "Aircraft model": model,
                "STAR": star_id,
                "%MLW": int(pct_mlw),
                "Dist. STAR entry WP to IAF [km]": round(star_data["dist_km"], 2),
                "IAF": star_data["iaf"],
                "Alt. at STAR entry WP [m]": round(alt_entry_m, 1),
                "Time from STAR entry WP to IAF [s]": round(time_to_iaf_s, 1),
                "TOA_dt": toa_iaf,
                "TOA IAF": toa_iaf.strftime("%H:%M:%S"),
            }
        )

    # Ordenació per hora d'arribada (TOA a l'IAF) i seqüenciació
    df = pd.DataFrame(results)
    df = df.sort_values(by="TOA_dt").reset_index(drop=True)
    df["Seq. Order"] = df.index + 1

    # Separació respecte a l'aeronau precedent a l'IAF
    separations = [None]
    for i in range(1, len(df)):
        dt = (df.loc[i, "TOA_dt"] - df.loc[i - 1, "TOA_dt"]).total_seconds()
        separations.append(round(dt, 1))

    df["Sep. to previous at IAF [s]"] = separations
    return df.drop(columns=["TOA_dt"])


if __name__ == "__main__":
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 1000)

    taula_resultat = compute_scenario_1()
    print("\n--- TAULA ESCENARI 1 (Simultaneous arrivals at 11:45:00 AM) ---")
    print(taula_resultat.to_string(index=False))