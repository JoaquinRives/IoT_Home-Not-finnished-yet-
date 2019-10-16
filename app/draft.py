 import app.config.config as config

 n_days = 30
 
filename = str(config.APP_ROOT) + f"/static/chart_{n_days}_days.html"

print(filename)
