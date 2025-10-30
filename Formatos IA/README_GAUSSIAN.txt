
QUICKSTART — Gaussian CH₄ plume + inversion

Files:
  - gaussian_ch4.py          Core library (model + inversion + utilities)
  - example_synthetic.csv    Synthetic dataset ready to test

How to test (terminal):
  1) python gaussian_ch4.py --demo

How to use in a notebook/script:
  from gaussian_ch4 import (
      preprocess_and_invert, pasquill_sigma, gaussian_concentration,
      latlon_to_local_xy, rotate_to_wind_frame, simulate_dataset
  )

  # A) Run with synthetic data
  df = simulate_dataset(n_points=800, Q_true_gps=0.25, stability="D")
  stats = preprocess_and_invert(df)
  print(stats)  # {'Q_hat_gps': ..., 'Q_hat_gph': ..., 'R2': ..., ...}

  # B) Run with your CSV (columns required):
  # lat, lon, z_m, ch4_ppm, background_ppm, wind_speed_ms, wind_dir_from_deg,
  # stability, source_lat, source_lon, source_height_m
  import pandas as pd
  df_real = pd.read_csv("your_file.csv")
  out = preprocess_and_invert(df_real, stability_override=None)
  print(out)

Notes:
  - The sigma parameterization uses smooth power-law fits per stability class (A–F).
    Treat them as starting defaults; calibrate with site data when available.
  - Units: Q in g/s (multiply by 3600 for g/h). Wind in m/s. Distances in m.
  - Ensure timestamps are synchronized and background is representative.
