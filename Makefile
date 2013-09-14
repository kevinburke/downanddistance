venv:
	virtualenv venv

install: venv
	. venv/bin/activate; pip install -r requirements.txt

serve:
	. venv/bin/activate; PORT=7007 python app.py
