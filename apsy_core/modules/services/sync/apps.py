import os
import json

MANIFEST_PATH = os.path.join(
	os.path.dirname(__file__),
	"manifest"
)

SYNC_APPS = {

	"marcas": {
		"empleados",
		"tipo_marcas_empleados",
		"marcas_empleados"
	},

	"apsy_go": {
		"tipo_clientes",
		"monedas",
		"unidades",

		"clientes",
		"telefonos",
		"correos",
		"direccion",

		"productos",
		"productos_precios",

		"rutas",
		"clientes_rutas",

		"inventario",

		"cierre_caja",
		"detalle_cierre_caja"
	}

}

def load_manifest(app):

	tablas = SYNC_APPS.get(app)

	if tablas is None:
		return None


	path = os.path.join(
		MANIFEST_PATH,
		app
	)

	manifest = {}

	# =========================
	# BASE
	# =========================

	base_path = os.path.join(
		path,
		"base.json"
	)

	with open(
		base_path,
		"r",
		encoding="utf-8"
	) as f:

		manifest = json.load(f)

	# =========================
	# TABLAS
	# =========================

	manifest["tables"] = []

	for tabla in tablas:

		file_path = os.path.join(
			path,
			f"{tabla}.json"
		)

		if not os.path.exists(file_path):
			raise Exception(
				f"Manifest no encontrado: {file_path}"
			)

		with open(
			file_path,
			"r",
			encoding="utf-8"
		) as f:

			manifest["tables"].append(
				json.load(f)
			)

	return manifest